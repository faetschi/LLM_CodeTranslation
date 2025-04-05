import os
import time
import requests
import pika
import re
import json
import subprocess
import logging
import shutil
import stringcase
import wordninja
import sys

from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Configuration ---
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")
MODEL_NAME = os.getenv("LLM_MODEL")
MAX_RETRIES = int(os.getenv("MAX_TRANSLATION_RETRIES", 5))

UPLOAD_DIR = "/fastapi/uploads/"
TEMP_DIR = "/translation_worker/temp/"
TRANSLATED_DIR = "/output/"
OLLAMA_URL = "http://ollama:11434/api/generate"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TRANSLATED_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def connect_to_rabbitmq():
    """Connects to RabbitMQ with retries."""
    retries = 5
    for i in range(retries):
        try:
            logging.info("Connecting to RabbitMQ...")
            # Increased heartbeat interval for potentially long-running tasks
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', heartbeat=600, blocked_connection_timeout=300))
            logging.info("Connected to RabbitMQ!")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            logging.warning(f"RabbitMQ not available. Retrying {i+1}/{retries}... Error: {e}")
            time.sleep(10) # Increased sleep time
    logging.error("Failed to connect to RabbitMQ after multiple retries.")
    raise Exception("Failed to connect to RabbitMQ after multiple retries.")

# --- Core Translation Logic ---
def translate_code(file_id, original_filename, custom_prompt=None, headers=None, cpp_test_file=None):
    headers = headers or {}
    """ Translates a C++ file to Java, attempting compilation and using an LLM
    to iteratively fix errors up to MAX_RETRIES times. Notifies test worker
    on completion (success or failure). """

    cpp_file_path = os.path.join(UPLOAD_DIR, original_filename)
    base_name = os.path.splitext(original_filename)[0]
    pascal_case_name = to_pascal_case(base_name)

    translated_folder_path = os.path.join(TRANSLATED_DIR, pascal_case_name)
    os.makedirs(translated_folder_path, exist_ok=True)

    temp_java_file_path = os.path.join(TEMP_DIR, f"{pascal_case_name}.java")
    final_java_file_path = os.path.join(translated_folder_path, f"{pascal_case_name}.java")
    failed_java_file_path = os.path.join(translated_folder_path, f"{pascal_case_name}_failed.java")

    # Initialize status variables
    success = False
    final_status = "failed" # Assume failure initially
    output_file_path = None # Path to send in notification

    try:
        if not os.path.exists(cpp_file_path):
            logging.error(f"C++ source file {cpp_file_path} not found for job {file_id}!")
            raise FileNotFoundError(f"🛑 Cannot find .cpp file to translate: {cpp_file_path}")

        logging.info(f"Processing {original_filename} -> {pascal_case_name}.java (Job ID: {file_id})")

        with open(cpp_file_path, "r", encoding='utf-8') as file: # Specify encoding
             cpp_code = file.read()

        ###########################
        ### INITIAL TRANSLATION ###
        ###########################
        logging.info(f"Starting initial translation for {pascal_case_name}.java")
        
        # Create header block for context (if any)
        header_snippets = ""
        if headers:
            header_snippets = "\n===== INCLUDED HEADER FILES (.h) =====\n" + "\n\n".join(
                f"// HEADER: {name}\n{content}" for name, content in headers.items()
            )
            
        # Custom user prompt gets added at the end as clarification
        custom_prompt_section = ""
        if custom_prompt:
            custom_prompt_section = (
                "\n\nAdditional instructions for this translation:\n"
                f"{custom_prompt.strip()}"
            )
        
        cpp_hints = extract_cpp_hints(cpp_code)
        
        full_prompt = (
                f"Translate the following C++ source file into idiomatic, fully compilable Java 17 code."
                f"{header_snippets}\n\n"
                f"===== C++ SOURCE FILE =====\n{cpp_code}\n\n"
                f"Translation Guidelines:\n"
                f"- Translate all logic, including edge cases, input validation, branching conditions, and error handling, with strict one-to-one functional fidelity.\n"
                f"- Do not simplify, rephrase, or restructure any control flow or behavior. The resulting Java code must behave identically in all runtime scenarios, including edge cases and error states.\n"       
                f"- The main public class must be named exactly \"{pascal_case_name}\".\n"
                f"- Maintain function and method signatures semantically equivalent to the original C++ version, including return types, parameters, optional arguments, and any method overloading.\n"
                f"- Preserve original variable and method names where possible to maintain structural traceability between C++ and Java versions. This helps in matching logic and simplifies validation.\n"
                f"- Avoid any form of refactoring, optimization, or code simplification. The priority is a direct, functionally equivalent translation, not idiomatic refinement.\n\n"
                f"After outputting the Java file, double-check that:\n"
                f"- All branches, loops, and conditionals from the C++ file are represented.\n"
                f"- The behavior of all functions remain precisely the same as the original C++ implementation.\n"
                f"- No logic has been omitted, reordered, or reinterpreted.\n"
                f"{cpp_hints}\n\n"
                f"{custom_prompt_section}\n"
        )
        
        initial_payload = {
            "model": MODEL_NAME,
            "system": SYSTEM_PROMPT,
            "prompt": full_prompt,
            "options": {            
                "num_ctx": 4000         # max context window size, default 2048 tokens, qwen2.5-coder limit 32,768
            },
            "stream": False,
        }

        try:
            response = requests.post(OLLAMA_URL, json=initial_payload, timeout=180) # Increased timeout
            response.raise_for_status()
            response_json = response.json()
            full_response = response_json.get("response", "").strip()

            # Extract code, removing potential markdown fences
            match = re.search(r"```(?:java)?\s*(.*?)```", full_response, re.DOTALL | re.IGNORECASE)
            current_java_code = match.group(1).strip() if match else full_response

            if not current_java_code:
                 logging.error("Initial translation returned empty code. Aborting.")
                 # success remains False, finally block will notify failure
                 return

        except requests.exceptions.RequestException as e:
            logging.exception(f"HTTP request failed during initial translation for {pascal_case_name}.java: {e}")
            # success remains False, finally block will notify failure
            return # Exit if initial translation fails

        ##################################
        ### COMPILATION AND RETRY LOOP ###
        ##################################
        compile_log = ""
        previous_sanitized_log = ""

        for attempt in range(MAX_RETRIES + 1): # +1 for initial attempt + MAX_RETRIES retries
            logging.info(f"--- Attempt {attempt + 1}/{MAX_RETRIES + 1} for {pascal_case_name}.java ---")

            # Ensure current_java_code is valid
            if not isinstance(current_java_code, str) or not current_java_code.strip():
                logging.error(f"Invalid or empty Java code content detected on attempt {attempt + 1}. Aborting.")
                success = False
                break # Exit loop if code is invalid

            code_with_declaration = add_language_declaration(current_java_code, "java", pascal_case_name)
            try:
                with open(temp_java_file_path, "w", encoding='utf-8') as output_file:
                    output_file.write(code_with_declaration)
            except IOError as e:
                logging.error(f"Failed to write temporary file {temp_java_file_path}: {e}")
                success = False
                break # Cannot proceed if writing fails

            logging.info(f"Compiling {temp_java_file_path}...")
            compile_success, compile_log = compile_java_file(temp_java_file_path)
            sanitized_log = sanitize_log(compile_log)

            if compile_success:
                logging.info(f"Compilation successful on attempt {attempt + 1}.")
                try:
                    shutil.copy(temp_java_file_path, final_java_file_path)
                    logging.info(f"Successfully compiled code copied to {final_java_file_path}")
                    if os.path.exists(failed_java_file_path):
                        try:
                            os.remove(failed_java_file_path)
                            logging.info(f"Removed previous failed file marker: {failed_java_file_path}")
                        except OSError as rm_err:
                            logging.warning(f"Could not remove previous failed file {failed_java_file_path}: {rm_err}")
                    success = True # Set success to True
                    output_file_path = final_java_file_path # Set the path for notification
                    break # Exit loop on success
                except Exception as e:
                    logging.error(f"Failed to copy successful file from {temp_java_file_path} to {final_java_file_path}: {e}")
                    success = False # Mark as failed if copy fails
                    output_file_path = None # No valid final file
                    break # Exit loop

            # --- Compilation Failed ---
            logging.warning(f"Compilation failed on attempt {attempt + 1}.")
            logging.info(f"Current Compilation Errors (Sanitized):\n{sanitized_log}")

            if attempt >= MAX_RETRIES:
                logging.error(f"Maximum retries ({MAX_RETRIES}) reached for {pascal_case_name}.java. Saving last failed attempt.")
                success = False # Explicitly ensure failure
                try:
                    # Use the code that was actually compiled (with declaration)
                    with open(failed_java_file_path, "w", encoding='utf-8') as failed_file:
                        failed_file.write(code_with_declaration)
                    logging.info(f"Last failing code saved to {failed_java_file_path}")
                    output_file_path = failed_java_file_path # Set failed path for notification
                    if os.path.exists(final_java_file_path):
                        try:
                            os.remove(final_java_file_path)
                            logging.info(f"Removed existing final file: {final_java_file_path}")
                        except OSError as rm_err:
                             logging.warning(f"Could not remove final file {final_java_file_path} after max retries: {rm_err}")
                except IOError as e:
                     logging.error(f"Failed to write final (failed) file {failed_java_file_path}: {e}")
                     output_file_path = None # Failed to save, no path to notify
                break # Exit loop after max retries

            # --- Prepare for Retry ---
            logging.info(f"Attempting LLM correction (Retry {attempt + 1}/{MAX_RETRIES}).")
            # pmd_log = run_pmd_analysis(temp_java_file_path) # Optional

            # *** CONSTRUCT RETRY PROMPT WITH HISTORY ***
            retry_prompt_parts = [
                 f"The following Java code, intended to be saved as \"{pascal_case_name}.java\", failed compilation on attempt {attempt + 1}.",
                 f"\n\n===== CURRENT JAVA CODE (Attempt {attempt + 1}) =====\n{current_java_code}", # Send code *without* package decl
                 f"\n\n===== CURRENT COMPILATION ERRORS (Attempt {attempt + 1}) =====\n{sanitized_log}"
            ]
            if previous_sanitized_log:
                 retry_prompt_parts.append(f"\n\n===== PREVIOUS COMPILATION ERRORS (Attempt {attempt}) =====\n{previous_sanitized_log}")
                 retry_prompt_parts.append(
                     "\n\nYour previous attempt resulted in the errors shown above ('PREVIOUS COMPILATION ERRORS'). "
                     "Analyze BOTH the 'CURRENT' and 'PREVIOUS' errors carefully. "
                     "DO NOT repeat the same mistakes. Identify the root cause and provide a significantly improved version."
                 )
            else:
                 retry_prompt_parts.append("\n\nThis is the first attempt to fix the initial translation.")

            retry_prompt_parts.append(
                 f"\n\nPlease correct the code to fix all current compilation errors. Strictly follow these rules:\n"
                 f"1. Ensure the file contains exactly one top-level public class named \"{pascal_case_name}\".\n"
                 f"2. Resolve all symbol errors 'cannot find symbol' (missing methods, types, variables, incorrect references) by adding all necessary import statements at the very top.\n"
                 f"3. Adjust access modifiers (public, private, protected) correctly.\n"
                 f"4. Fix invalid method declarations, constructors, and return types.\n"
                 f"5. Ensure helper classes are defined correctly (top-level non-public or properly nested).\n"
                 f"6. Adhere strictly to Java 17 syntax and conventions.\n"
                 f"7. Focus on fixing the root causes identified in the compilation error log, ensuring issues from the *previous* log (if any) are also resolved.\n\n"
                 f"Output *only* the corrected, complete Java source code. Do not include explanations, comments outside the code, or markdown formatting."
            )

            retry_payload = {
                "model": MODEL_NAME,
                "system": SYSTEM_PROMPT,
                "prompt": "".join(retry_prompt_parts),
                "options": {            
                    "num_ctx": 4000         # max context window size, default 2048 tokens, qwen2.5-coder limit 32,768
                },
                "stream": False,
            }
            # *** END RETRY PROMPT CONSTRUCTION ***

            try:
                logging.info(f"Sending correction request to Ollama (Attempt {attempt + 2} incoming)...")
                retry_response = requests.post(OLLAMA_URL, json=retry_payload, timeout=180) # Increased timeout
                retry_response.raise_for_status()

                retry_result = retry_response.json().get("response", "").strip()
                retry_match = re.search(r"```(?:java)?\s*(.*?)```", retry_result, re.DOTALL | re.IGNORECASE)
                fixed_code = retry_match.group(1).strip() if retry_match else retry_result

                if not fixed_code:
                    logging.warning(f"LLM correction attempt {attempt + 1} returned empty code. Re-using previous code for next attempt.")
                    # Keep previous_sanitized_log as is
                    continue # Skip updating current_java_code and proceed to next attempt or max retries

                # Force the public class name
                fixed_code = re.sub(r'\bpublic\s+(?:final\s+|abstract\s+)?class\s+\w+\b', f'public class {pascal_case_name}', fixed_code, count=1)

                current_java_code = fixed_code
                logging.info(f"Received corrected code from LLM for attempt {attempt + 2}.")

            except requests.exceptions.RequestException as e:
                logging.error(f"Error during LLM retry request for {pascal_case_name}.java: {e}")
                success = False
                logging.error("Aborting retries due to LLM request error.")
                try:
                    # Save the code *before* the failed LLM call attempt (which failed compilation)
                    with open(failed_java_file_path, "w", encoding='utf-8') as failed_file:
                        failed_file.write(code_with_declaration) # Save the version that failed compilation
                    logging.info(f"Last code that failed compilation before LLM error saved to {failed_java_file_path}")
                    output_file_path = failed_java_file_path # Set path for notification
                    if os.path.exists(final_java_file_path):
                         try:
                             os.remove(final_java_file_path)
                             logging.info(f"Removed existing final file: {final_java_file_path}")
                         except OSError as rm_err:
                             logging.warning(f"Could not remove final file {final_java_file_path} after LLM error: {rm_err}")
                except IOError as io_e:
                    logging.error(f"Failed to write failed file {failed_java_file_path} after LLM error: {io_e}")
                    output_file_path = None # Failed to save, no path
                break # Exit loop on LLM error

            # Store the errors from THIS failed attempt for the NEXT retry
            previous_sanitized_log = sanitized_log

        # --- Loop finished or broke ---
        final_status = "success" if success else "failed"
        logging.info(f"--- Translation process finished for {pascal_case_name}.java ---")
        logging.info(f"Final status: {final_status.upper()}")
        if not success and output_file_path is None and os.path.exists(failed_java_file_path):
            # If loop finished due to some other reason but failed file exists
             output_file_path = failed_java_file_path
             logging.info(f"Using {failed_java_file_path} as output path for failure notification.")


    except FileNotFoundError as e:
         # This specific case is handled above, but catch again just in case.
         logging.error(f"File not found error during translation process for {file_id}: {e}")
         final_status = "failed"
         output_file_path = None
    except Exception as e:
         # Catch any other unexpected errors during the whole process
         logging.exception(f"Unhandled exception while translating {file_id} ({original_filename}): {e}")
         final_status = "failed"
         # Try to set failed path if it might exist, otherwise None
         output_file_path = failed_java_file_path if os.path.exists(failed_java_file_path) else None

    finally:
        ################################
        ### NOTIFICATION AND CLEANUP ###
        ################################
        logging.info(f"--- Finalizing job for {pascal_case_name}.java (Status: {final_status.upper()}) ---")

        # Ensure output_file_path reflects reality if success=True but file is missing
        if final_status == "success" and not os.path.exists(final_java_file_path):
            logging.error(f"Status is 'success' but final file '{final_java_file_path}' not found! Reporting failure.")
            final_status = "failed"
            output_file_path = None

        # Ensure output_file_path reflects reality if success=False but failed_file is missing
        if final_status == "failed" and output_file_path == failed_java_file_path and not os.path.exists(failed_java_file_path):
             logging.warning(f"Status is 'failed' and expected failed file '{failed_java_file_path}' not found. Sending notification without specific path.")
             output_file_path = None

        # *** Send notification regardless of success/failure ***
        #notify_test_generation_worker(pascal_case_name, final_status, output_file_path, cpp_test_file)

        # Cleanup temporary Java and class files
        cleanup_temp_and_class_files(pascal_case_name)

        # Remove original C++ file after processing
        try:
            if cpp_file_path and os.path.exists(cpp_file_path): # Check if cpp_file_path was defined
                os.remove(cpp_file_path)
                logging.info(f"🧹 Removed original .cpp file: {os.path.basename(cpp_file_path)}")
        except NameError:
             logging.warning("⚠️ Original C++ file path variable not defined, skipping removal.")
        except Exception as e:
            logging.warning(f"⚠️ Could not remove original .cpp file {cpp_file_path}: {e}")

# --- Notification ---
from typing import Optional

def notify_test_generation_worker(pascal_case_name: str, status: str, file_path: Optional[str], cpp_test_file=None):
    """Sends a message to RabbitMQ to trigger test generation, including status."""
    try:
        logging.info(f"Attempting to notify Test Generation Worker for {pascal_case_name} (Status: {status.upper()})...")

        connection = connect_to_rabbitmq()
        channel = connection.channel()

        queue_name = 'test_generation_queue'
        channel.queue_declare(queue=queue_name, durable=True)

        message = {
            "action": "generate_test",
            "pascal_case_name": pascal_case_name,
            "translation_status": status, # 'success' or 'failed'
            "java_file_path": file_path   # Full path to .java (success) or _failed.java (failure), or None
        }
        
        if cpp_test_file:
            message["cpp_test_reference"] = cpp_test_file

        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
            )
        )

        log_path_str = f", Path: {file_path}" if file_path else ""
        logging.info(f"Sent message to '{queue_name}' for {pascal_case_name} (Status: {status.upper()}{log_path_str})")
        connection.close()

    except Exception as e:
        # Log detailed error including message content if possible
        log_path_str = f", Path: {file_path}" if file_path else ""
        logging.error(f"Error sending message to Test Generation Worker for {pascal_case_name} (Status: {status.upper()}{log_path_str}): {e}", exc_info=True)
        # Consider what to do if notification fails - retry? Log?


# --- Compilation ---
def compile_java_file(java_file_path: str) -> tuple[bool, str]:
    """Compiles the Java file and returns success status and log."""
    # Ensure TEMP_DIR exists before compiling into it
    os.makedirs(TEMP_DIR, exist_ok=True)

    compile_command = ["javac", "-Xlint:all", "--release", "17", "-d", TEMP_DIR, java_file_path] # Specify Java 17, output .class to TEMP_DIR
    logging.debug(f"Running compilation command: {' '.join(compile_command)}")
    try:
        result = subprocess.run(
            compile_command,
            capture_output=True,
            text=True,
            check=False, # Don't raise error on non-zero exit, check result.returncode instead
            timeout=30 # Slightly longer timeout for javac
        )
        # Check return code explicitly
        if result.returncode == 0:
             # Compilation succeeded, stderr might contain warnings
             logging.debug(f"Compilation successful (rc=0). Warnings (stderr):\n{result.stderr or '[None]'}")
             return True, result.stderr # Return warnings if any
        else:
             # Compilation failed
             error_output = result.stderr if result.stderr else result.stdout # Errors usually go to stderr
             logging.warning(f"Compilation failed (rc={result.returncode}) for {java_file_path}.")
             logging.debug(f"javac stdout:\n{result.stdout or '[None]'}") # Log both streams on error
             logging.debug(f"javac stderr:\n{result.stderr or '[None]'}")
             return False, error_output

    except subprocess.TimeoutExpired:
        logging.error(f"Compilation timed out for {java_file_path}")
        return False, "Compilation timed out after 30 seconds"
    except FileNotFoundError:
         logging.error("Error: 'javac' command not found. Make sure JDK 17+ is installed and in PATH.")
         return False, "'javac' command not found."
    except Exception as e:
        logging.error(f"Unexpected error during compilation: {e}", exc_info=True)
        return False, f"Unexpected compilation error: {str(e)}"


# --- Cleanup ---
def cleanup_temp_and_class_files(pascal_case_name=None):
    """
    Cleans up ALL files and subdirectories within TEMP_DIR.
    Cleans up .class files in the specific subfolder under TRANSLATED_DIR if pascal_case_name is provided.
    """
    # --- Clean TEMP_DIR Thoroughly ---
    logging.info(f"Attempting thorough cleanup of TEMP_DIR: {TEMP_DIR}")
    if not os.path.isdir(TEMP_DIR):
        logging.debug(f"TEMP_DIR {TEMP_DIR} does not exist or is not a directory. Skipping TEMP_DIR cleanup.")
    else:
        for item_name in os.listdir(TEMP_DIR):
            item_path = os.path.join(TEMP_DIR, item_name)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.remove(item_path)
                    #logging.debug(f"🧹 Removed temp file/link: {item_path}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    #logging.debug(f"🧹 Removed temp directory: {item_path}")
            except FileNotFoundError:
                 # Item might have been removed by another concurrent process or already gone
                 logging.debug(f"⚠️ File/directory not found during TEMP_DIR cleanup (might be okay): {item_path}")
            except PermissionError as pe:
                 logging.error(f"🚫 Permission error deleting temp item {item_path}: {pe}.")
            except OSError as oe:
                 logging.error(f"💥 OS error deleting temp item {item_path}: {oe}")
            except Exception as e:
                 logging.error(f"💥 Failed to delete temp item {item_path}: {e}", exc_info=True)
        logging.info("Finished TEMP_DIR cleanup attempt.")


    # --- Clean .class files in the specific TRANSLATED_DIR subfolder ---
    if pascal_case_name:
        translated_subfolder_path = os.path.join(TRANSLATED_DIR, pascal_case_name)
        if os.path.isdir(translated_subfolder_path):
            logging.info(f"Cleaning up .class files in translated folder: {translated_subfolder_path}")
            class_files_found = False
            for filename in os.listdir(translated_subfolder_path):
                if filename.endswith(".class"):
                    class_files_found = True
                    file_path = os.path.join(translated_subfolder_path, filename)
                    try:
                        os.remove(file_path)
                        #logging.debug(f"🧹 Removed .class file: {file_path}")
                    except FileNotFoundError:
                        logging.warning(f"⚠️ .class file not found during cleanup: {file_path}")
                    except PermissionError as pe:
                        logging.error(f"🚫 Permission error deleting .class file {file_path}: {pe}")
                    except Exception as e:
                        logging.warning(f"⚠️ Failed to delete .class file {file_path}: {e}")
            if not class_files_found:
                 logging.debug(f"No .class files found in {translated_subfolder_path} to clean up.")
            else:
                 logging.info(f"Finished .class file cleanup in {translated_subfolder_path}.")

        else:
             logging.debug(f"Translated folder {translated_subfolder_path} not found for .class cleanup.")

            
# --- PMD Analysis (Optional) ---
def run_pmd_analysis(java_file_path: str) -> str:
    """Runs PMD analysis and returns filtered output."""
    pmd_command = [
        "pmd", "check",
        "-d", java_file_path,
        "-R", "rulesets/java/quickstart.xml", # Ensure this ruleset exists or use a default one
        "-f", "text"
    ]
    logging.info(f"Running PMD command: {' '.join(pmd_command)}")
    try:
        result = subprocess.run(
            pmd_command,
            capture_output=True,
            text=True,
            check=True, # Let it fail if PMD itself fails
            timeout=30 # PMD can be slower
        )
        output = result.stdout
        # Filter out common noise lines from PMD output
        processed_lines = [
            line.strip() for line in output.splitlines()
            if line.strip() and
               "Progressbar" not in line and
               "Incremental Analysis" not in line and
               "Ruleset not found" not in line and # Example of another filter
               "Deprecated ruleset" not in line
        ]
        final_output = "\n".join(processed_lines).strip()
        logging.info(f"PMD Analysis completed for {java_file_path}.")
        return final_output if final_output else "No PMD violations found."
    except subprocess.CalledProcessError as e:
        error_output = e.stderr if e.stderr else e.stdout
        logging.warning(f"PMD command failed for {java_file_path}: {error_output}")
        return f"PMD analysis failed:\n{error_output}"
    except FileNotFoundError:
         logging.error("Error: 'pmd' command not found. Make sure PMD is installed and in PATH.")
         return "'pmd' command not found."
    except subprocess.TimeoutExpired:
        logging.warning(f"PMD analysis timed out for {java_file_path}")
        return "PMD analysis timed out after 30 seconds"
    except Exception as e:
        logging.warning(f"PMD analysis encountered an unexpected error: {e}")
        return f"PMD analysis error: {str(e)}"


# --- Helper Methods ---
def add_language_declaration(code: str, language: str, identifier: str) -> str:
    """Adds a Java package declaration if not already present."""
    if language.lower() == "java":
        # Regex to find package declaration, allowing for comments/whitespace before it
        package_pattern = re.compile(rf"^\s*(//.*?\n|/\*.*?\*/\s*)*package\s+{re.escape(identifier)}\s*;", re.MULTILINE | re.DOTALL)
        if not package_pattern.search(code):
            lines = code.splitlines()
            insert_pos = 0
            # Find the first line that is not a comment or whitespace
            for i, line in enumerate(lines):
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith(('//', '/*')):
                    # Check if it's an import or class definition - package should go before
                    if stripped_line.startswith(('import ', 'public ', 'class ', 'interface ', '@')):
                        insert_pos = i
                        break
                    # If it's something else, maybe put package just before it anyway? Or log warning?
                    # For now, assume first non-comment is where package should go above.
                    insert_pos = i
                    break
                elif not stripped_line: # Keep track of empty lines at the start
                     insert_pos = i + 1


            # Insert package declaration and a blank line
            lines.insert(insert_pos, f"package {identifier};")
            # Add blank line only if there isn't one already after insertion point
            if insert_pos + 1 >= len(lines) or lines[insert_pos + 1].strip():
                 lines.insert(insert_pos + 1, "")
            return "\n".join(lines)
        else:
            return code # Already has a package declaration
    else:
        return code

def to_pascal_case(s: str) -> str:
    """Converts a string to PascalCase, handling various delimiters and splitting words."""
    if not s:
        return "DefaultClassName" # Handle empty input

    # Normalize delimiters to spaces first
    s = re.sub(r'[-_\s]+', ' ', s).strip()

    # If it looks like camelCase or already PascalCase, try splitting based on case changes
    if not ' ' in s and (re.search(r'[a-z][A-Z]', s) or re.match(r'[A-Z][a-z]', s)):
         words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+', s)
    # Otherwise, split by spaces (after normalization)
    elif ' ' in s:
        words = s.split(' ')
    # If it's just a single block (e.g., all lowercase, all uppercase, or with digits), use wordninja as fallback
    else:
         # Separate any trailing digits first to help wordninja
        m = re.match(r'^(.*?)(\d+)$', s)
        if m:
            base = m.group(1)
            suffix = m.group(2)
        else:
            base = s
            suffix = ""
        # Use wordninja only if base is not empty
        ninja_words = wordninja.split(base) if base else []
        words = [word.capitalize() for word in ninja_words]
        return ''.join(words) + suffix

    # Capitalize each word and join
    pascal_cased = ''.join(word.capitalize() for word in words if word)

    # Ensure the result starts with a letter and contains only valid Java identifier characters
    # Remove invalid characters
    pascal_cased = re.sub(r'[^a-zA-Z0-9_]', '', pascal_cased)
    # Ensure it starts with a letter or underscore
    if not re.match(r'^[a-zA-Z_]', pascal_cased):
        pascal_cased = "Generated_" + pascal_cased

    return pascal_cased if pascal_cased else "DefaultClassName"


def sanitize_log(log_text, max_lines=50, max_chars=5000):
    """Takes the first N lines and limits total characters of a log."""
    if not log_text:
        return "[No compilation output]"
    lines = log_text.splitlines()
    limited_lines = '\n'.join(lines[:max_lines])
    # Limit total characters to prevent excessively large logs in LLM prompts
    if len(limited_lines) > max_chars:
        return limited_lines[:max_chars] + "\n... [Log Truncated]"
    return limited_lines

# --- C++ Hints Extraction ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    profiles_dir = os.path.join(script_dir, 'profiles')
    sys.path.append(profiles_dir)
    from profiles.cpp_patterns import detect_cpp_patterns
    logging.info("Successfully imported 'detect_cpp_patterns'.")
except ImportError:
    logging.warning("Could not import 'detect_cpp_patterns'. C++ hints will be disabled.")
    logging.warning(f"Looked for profiles directory at: {profiles_dir}")
    def detect_cpp_patterns(code: str) -> list: return []
except Exception as e:
     logging.error(f"Error importing or setting up 'detect_cpp_patterns': {e}")
     def detect_cpp_patterns(code: str) -> list: return []

def extract_cpp_hints(cpp_code: str) -> str:
    """Extracts hints using the imported C++ pattern detector."""
    try:
        hints = detect_cpp_patterns(cpp_code)
        if hints:
            return "Hints provided from the C++ code:\n" + "\n".join(hints)
        else:
            return ""
    except Exception as e:
        logging.warning(f"Error during C++ hint extraction: {e}")
        return "Hint extraction failed."

###############
### GENERAL ###                    
###############

# --- Worker ---
def start_worker():
    """Main worker loop connecting to RabbitMQ and processing tasks."""
    logging.info("Starting Translation Worker...")
    while True:
        connection = None # Ensure connection is reset in loop
        try:
            connection = connect_to_rabbitmq()
            channel = connection.channel()
            queue_name = "translation_queue"
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_qos(prefetch_count=1) # Process one message at a time

            def callback(ch, method, properties, body):
                start_time = time.time()
                file_id = None
                original_filename = None
                try:
                    message = json.loads(body.decode())
                    file_id = message.get("file_id")
                    original_filename = message.get("cpp_filename")
                    cpp_test_file = message.get("cpp_test_file")
                    custom_prompt = message.get("custom_prompt")
                    headers = message.get("headers", {})

                    if not file_id or not original_filename:
                         raise ValueError("Missing 'file_id' or 'filename' in message")

                    logging.info(f"Received job: file_id={file_id}, filename={original_filename}")
                    # Optional short delay if needed, but usually processing starts immediately
                    # time.sleep(1)
                    translate_code(file_id, original_filename, custom_prompt, headers, cpp_test_file)
                    processing_time = time.time() - start_time
                    logging.info(f"Finished job for {original_filename} in {processing_time:.2f} seconds. Sending ACK.")
                    ch.basic_ack(delivery_tag=method.delivery_tag)

                except json.JSONDecodeError as json_err:
                    logging.error(f"Failed to parse message body: {body.decode()} - Error: {json_err}")
                    # Acknowledge the message even if parsing fails to prevent it from being redelivered indefinitely
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except ValueError as val_err:
                     logging.error(f"Invalid message content: {val_err} - Message: {body.decode()}")
                     ch.basic_ack(delivery_tag=method.delivery_tag) # Ack invalid message
                except Exception as process_err:
                    processing_time = time.time() - start_time
                    logging.exception(f"Error processing job for file_id={file_id}, filename={original_filename} after {processing_time:.2f}s: {process_err}")
                    # Negative Acknowledge (NACK) and requeue=False (or True if you want RabbitMQ to retry)
                    # NACKing without requeue sends it to a dead-letter queue if configured, otherwise drops it.
                    # Choose carefully based on whether the error is likely temporary or permanent.
                    # For now, let's ACK to avoid potential infinite loops if the error is persistent for this message.
                    logging.warning("Acknowledging message despite processing error to avoid requeue loop.")
                    ch.basic_ack(delivery_tag=method.delivery_tag)


            channel.basic_consume(queue=queue_name, on_message_callback=callback)
            logging.info(f"Worker is waiting for tasks on queue '{queue_name}'...")
            channel.start_consuming()

        except pika.exceptions.ConnectionClosedByBroker:
            logging.warning("Connection closed by RabbitMQ broker. Retrying connection in 5s...")
        except pika.exceptions.AMQPChannelError as err:
            logging.error(f"Caught a channel error: {err}. Restarting worker in 5s...")
        except pika.exceptions.AMQPConnectionError as err:
             logging.error(f"Caught a connection error: {err}. Retrying connection in 5s...")
        except Exception as e:
            logging.exception(f"Unexpected error in worker loop: {e}. Restarting worker in 5s...")
        finally:
            # Ensure connection is closed if it was opened, before retrying
            if connection and not connection.is_closed:
                try:
                    connection.close()
                    logging.info("RabbitMQ connection closed.")
                except Exception as ce:
                     logging.error(f"Error closing RabbitMQ connection: {ce}")
            logging.info("Waiting 5 seconds before restarting worker...")
            time.sleep(5)

if __name__ == "__main__":
    start_worker()
