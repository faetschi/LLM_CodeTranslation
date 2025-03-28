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

from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")
MODEL_NAME = os.getenv("LLM_MODEL")

UPLOAD_DIR = "/fastapi/uploads/"
TEMP_DIR = "/translation_worker/temp/"
TRANSLATED_DIR = "/translation_worker/translated/"
OLLAMA_URL = "http://ollama:11434/api/generate"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TRANSLATED_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def connect_to_rabbitmq():
    retries = 5
    for i in range(retries):
        try:
            logging.info("Connecting to RabbitMQ...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            logging.info("Connected to RabbitMQ!")
            return connection
        except pika.exceptions.AMQPConnectionError:
            logging.warning(f"RabbitMQ not available. Retrying {i+1}/{retries}...")
            time.sleep(5)
    raise Exception("Failed to connect to RabbitMQ after multiple retries.")

def translate_code(file_id, original_filename):
    cpp_file_path = os.path.join(UPLOAD_DIR, f"{file_id}.cpp")
    base_name = os.path.splitext(original_filename)[0]
    pascal_case_name = to_pascal_case(base_name)
    
    # Create a folder for the translated Java file
    translated_folder_path = os.path.join(TRANSLATED_DIR, pascal_case_name)
    os.makedirs(translated_folder_path, exist_ok=True)
    
    temp_java_file_path = os.path.join(TEMP_DIR, f"{pascal_case_name}.java")
    final_java_file_path = os.path.join(translated_folder_path, f"{pascal_case_name}.java")

    if not os.path.exists(cpp_file_path):
        logging.error(f"File {cpp_file_path} not found!")
        return

    with open(cpp_file_path, "r") as file:
        cpp_code = file.read()
        
###########################
### INITIAL TRANSLATION ###                    
###########################

    cpp_hints = extract_cpp_hints(cpp_code)
    
    payload = {
        "model": MODEL_NAME,
        "system": SYSTEM_PROMPT,
        "prompt": (
            f'Translate the following C++ source file into idiomatic, fully compilable Java 17 code.\n\n'
            f'===== C++ SOURCE =====\n{cpp_code}\n\n'
            f'Guidelines:\n'
            f'- Output only valid Java source code with all necessary import statements at the top.\n'
            f'- The output must form a single, compilable Java 17 file.\n'
            f'- Ensure proper class structure: imports must be at the top, helper methods and classes must be correctly nested.\n'
            f'- The main public class must be named "{pascal_case_name}", matching the filename.\n'
            f'- When external C++ libraries are used, re-implement their purpose using modern Java standard libraries or popular open-source Java libraries.\n'
            f'- Do not mirror C++ syntax or library APIs. Instead, write idiomatic Java that achieves the same behavior.\n'
            f'- Use idiomatic Java patterns and standard libraries instead of C++-specific constructs or libraries.\n\n'
            f'Hints extracted from the C++ code:\n{cpp_hints}\n\n'
            f'- Output strictly one valid Java file, and nothing else.'
        ),
        "stream": False
    }

    try:
        logging.info(f"Sending translation request to Ollama with model '{MODEL_NAME}'")
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        response_json = response.json()
        full_response = response_json.get("response", "").strip()

        match = re.search(r"```(?:java)?\s*(.*?)```", full_response, re.DOTALL)
        java_code = match.group(1).strip() if match else full_response

       # Ensure the corresponding directory exists in TRANSLATED_DIR
        os.makedirs(os.path.dirname(final_java_file_path), exist_ok=True)

        # Add the appropriate start declaration for Java
        code_with_declaration = add_language_declaration(java_code, "java", pascal_case_name)

        with open(temp_java_file_path, "w") as output_file:
            output_file.write(code_with_declaration)

        logging.info(f"Initial translation saved to {temp_java_file_path}")
        success, compile_log = compile_java_file(temp_java_file_path)

        ## successful compilation
        if success:
            shutil.copy(temp_java_file_path, final_java_file_path)
            logging.info(f"Compilation successful. File copied to {final_java_file_path}")
            
            cleanup_temp_and_class_files(pascal_case_name)
            notify_test_generation_worker(pascal_case_name)
            
        #####################################
        ### RETRY PHASE AFTER COMPILATION ###                    
        #####################################
        else:
            logging.warning(f"Compilation failed. Attempting fix...")
            logging.info("Compile LOG: \n" + compile_log)
            sanitized_log = sanitize_log(compile_log)
            
            # Run PMD analysis to capture static analysis issues
            # TODO eig erst nachdem file fertig ist (um danach fehler zu finden)
            #pmd_log = run_pmd_analysis(temp_java_file_path)
            #logging.info("PMD LOG: \n" + pmd_log)
            
            retry_payload = {
                "model": MODEL_NAME,
                "system": SYSTEM_PROMPT,
                "prompt": (
                    f"The following Java code was generated from a C++ source file, but it fails to compile when saved as \"{pascal_case_name}.java\":\n\n"
                    f"===== JAVA CODE =====\n"
                    f"{java_code}\n\n"
                    f"===== COMPILATION ERRORS (first 50 lines) =====\n"
                    f"{sanitized_log}\n\n"
                    #f"===== Static Analysis Issues =====\n"
                    #f"{pmd_log}\n\n"
                    f"Please correct all the issues so that the code compiles as a valid Java 17 file. Address the following problems explicitly:\n"
                    f"1. The file contains exactly one public class, and its name is exactly \"{pascal_case_name}\" (do not output any public class named \"Main\").\n"
                    f"2. Resolve any symbol errors (for example, methods that are missing or incorrectly referenced).\n"
                    f"3. Adjust access modifiers so that methods meant to be called externally are declared public.\n"
                    f"4. Correct any invalid method declarations, ensure constructors or methods have the proper return types if required.\n"
                    f"5. Ensure that supporting classes are top-level classes, not nested.\n"
                    f"Each Java file should ideally contain one top-level public class only.\n\n"
                    f"The main public class must have the name \"{pascal_case_name}\" (the filename is \"{pascal_case_name}\" and the class name must match this name).\n"
                    f"Return only the corrected Java 17 code with no explanations, comments, or markdown formatting."
                ),
                "stream": False
            }
            
            retry_response = requests.post(OLLAMA_URL, json=retry_payload)
            retry_response.raise_for_status()
            
            #######################
            ### POST PROCESSING ###
            #######################

            retry_result = retry_response.json().get("response", "").strip()
            retry_match = re.search(r"```(?:java)?\s*(.*?)```", retry_result, re.DOTALL)
            
            fixed_code = retry_match.group(1).strip() if retry_match else retry_result
            #fixed_code = re.sub(r'public\s+class\s+Main\b', f'public class {pascal_case_name}', fixed_code)
            fixed_code = re.sub(r'\bpublic\s+(?:final\s+|abstract\s+)?class\s+Main\b', f'public class {pascal_case_name}', fixed_code)

            with open(final_java_file_path, "w") as output_file:
                output_file.write(fixed_code)

            retry_success, retry_log = compile_java_file(final_java_file_path)

            if retry_success:
                shutil.copy(temp_java_file_path, final_java_file_path)
                logging.info(f"Retry compilation succeeded. Final file copied to {final_java_file_path}")
                ### CLEAN temp files ###
                cleanup_temp_and_class_files(pascal_case_name)
                # send signal to test_generator worker that generates integration test of the newly created java file
                notify_test_generation_worker(pascal_case_name)
            else:
                failed_path = final_java_file_path.replace(".java", "_failed.java")
                logging.error(f"Retry failed again. Output saved to {failed_path}\n{retry_log}")
                ### CLEAN temp files ###
                cleanup_temp_and_class_files(pascal_case_name)
                # send signal to test_generator worker that generates integration test of the newly created java file
                notify_test_generation_worker(pascal_case_name)
                
            try:
                if os.path.exists(cpp_file_path):
                    os.remove(cpp_file_path)
                    logging.info(f"🧹 Removed original .cpp file: {os.path.basename(cpp_file_path)}")
            except Exception as e:
                logging.warning(f"⚠️ Could not remove original .cpp file: {cpp_file_path} — {e}")

    except Exception as e:
        logging.exception(f"Exception while translating {file_id}: {e}")
        

def notify_test_generation_worker(pascal_case_name):
    try:
        logging.info(f"Attempting to notify Test Generation Worker for {pascal_case_name}...")

        # Establish connection to RabbitMQ and create a channel
        connection = connect_to_rabbitmq()
        channel = connection.channel()

        # Declare the queue to make sure it exists
        channel.queue_declare(queue='test_generation_queue', durable=True)

        # Create the message to notify the Test Generation Worker
        message = {
            "action": "generate_test",
            "java_file": f"{TRANSLATED_DIR}/{pascal_case_name}/{pascal_case_name}.java"  # Full path
        }

        # Send the message to the test_generation_queue
        channel.basic_publish(
            exchange='',
            routing_key='test_generation_queue',  # Target queue for the test worker
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make the message persistent
            )
        )

        logging.info(f"Sent message to Test Generation Worker to generate test for {pascal_case_name}")
        
        # Close the connection to RabbitMQ
        connection.close()

    except Exception as e:
        logging.error(f"Error sending message to Test Generation Worker: {e}")

        
def compile_java_file(java_file_path: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["javac", java_file_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode("utf-8") if e.stderr else e.stdout.decode("utf-8")
        return False, error_output
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out"
            
        
def cleanup_temp_and_class_files(pascal_case_name=None):
    """
    Cleans up:
    - All `.class` files in TEMP_DIR and the corresponding folder in TRANSLATED_DIR (if pascal_case_name is provided).
    - All `.java` files in TEMP_DIR.
    Logs any remaining files in TEMP_DIR for verification.
    """
    try:
        # Cleanup .class files in TEMP_DIR
        logging.info(f"Cleaning up .class files in TEMP_DIR: {TEMP_DIR}")
        for filename in os.listdir(TEMP_DIR):
            if filename.endswith(".class"):
                file_path = os.path.join(TEMP_DIR, filename)
                try:
                    os.remove(file_path)
                    logging.info(f"🧹 Removed .class file: {file_path}")
                except Exception as e:
                    logging.warning(f"⚠️ Failed to delete .class file {file_path}: {e}")

        # Cleanup .class files in the corresponding folder under TRANSLATED_DIR if pascal_case_name is provided
        if pascal_case_name:
            translated_folder_path = os.path.join(TRANSLATED_DIR, pascal_case_name)
            logging.info(f"Cleaning up .class files in translated folder: {translated_folder_path}")
            
            if os.path.exists(translated_folder_path):
                logging.info(f"Files in translated folder: {os.listdir(translated_folder_path)}")
                
                # Walk through the translated folder to remove .class files
                for root, dirs, files in os.walk(translated_folder_path):
                    for filename in files:
                        if filename.endswith(".class"):
                            file_path = os.path.join(root, filename)
                            try:
                                os.remove(file_path)
                                logging.info(f"🧹 Removed .class file from translated folder: {file_path}")
                            except Exception as e:
                                logging.warning(f"⚠️ Failed to delete .class file from translated folder {file_path}: {e}")
            else:
                logging.warning(f"⚠️ Translated folder {translated_folder_path} does not exist.")

        # Remove all .java files in TEMP_DIR
        for filename in os.listdir(TEMP_DIR):
            if filename.endswith(".java"):
                file_path = os.path.join(TEMP_DIR, filename)
                try:
                    os.remove(file_path)
                    logging.info(f"🧹 Removed temp .java file: {file_path}")
                except Exception as e:
                    logging.warning(f"⚠️ Failed to delete .java file {file_path}: {e}")

        # Final check for leftover files in TEMP_DIR
        remaining = os.listdir(TEMP_DIR)
        if remaining:
            logging.warning(f"⚠️ TEMP_DIR still contains files: {remaining}")
        else:
            logging.info("✅ TEMP_DIR cleanup complete.")

    except Exception as e:
        logging.error(f"💥 Exception during cleanup: {e}")

            
def run_pmd_analysis(java_file_path: str) -> str:
    """
    Runs PMD analysis on the given Java file using the quickstart ruleset,
    removes internal warnings (e.g., progressbar and incremental analysis warnings),
    and returns only the log messages.
    If no violations are found, returns a default message.
    """
    try:
        result = subprocess.run(
            ["pmd", "check", "-d", java_file_path, "-R", "rulesets/java/quickstart.xml", "-f", "text"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15
        )
        output = result.stdout.decode("utf-8")
        processed_lines = []
        for line in output.splitlines():
            line_clean = line.strip()
            # Exclude lines that mention progressbar or incremental analysis warnings (default warnings)
            if "Progressbar" in line_clean or "Incremental Analysis" in line_clean:
                continue
            processed_lines.append(line_clean)
        final_output = "\n".join(processed_lines).strip()
        return final_output if final_output else "No PMD violations found."
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode("utf-8") if e.stderr else e.stdout.decode("utf-8")
        logging.warning(f"PMD analysis error: {error_output}")
        return error_output
    except Exception as e:
        logging.warning(f"PMD analysis failed: {e}")
        return ""

            
######################
### HELPER METHODS ###                    
######################

def add_language_declaration(code: str, language: str, identifier: str) -> str:
    """
    Adds a language-specific declaration to the top of the generated code.
    For example, adds `package <identifier>;` for Java, `import <identifier>;` for Python etc.
    
    :param code: The generated code.
    :param language: The target programming language (e.g., 'java', 'cpp', 'python').
    :param identifier: The identifier to use for the declaration (e.g., class name, package, etc.).
    :return: The code with the appropriate declaration added.
    """
    if language.lower() == "java":
        return f"package {identifier};\n\n" + code
    elif language.lower() == "python":
        return f"import {identifier}\n\n" + code
    else:
        return code  # Return code unchanged for unsupported languages

def to_pascal_case(s: str) -> str:
    # If the string contains delimiters, use stringcase directly.
    if re.search(r'[-_\s]', s):
        return stringcase.pascalcase(s)
    
    # Separate any trailing digits from the main word.
    m = re.match(r'^(.*?)(\d+)$', s)
    if m:
        base = m.group(1)
        suffix = m.group(2)
    else:
        base = s
        suffix = ""
    
    # Use wordninja to split concatenated lowercase words.
    words = wordninja.split(base)
    # Capitalize each word and append the numeric suffix.
    return ''.join(word.capitalize() for word in words) + suffix

def sanitize_log(log_text, max_lines=50):
    return '\n'.join(log_text.splitlines()[:max_lines])

### GIVE SPECIFIC HINTS ON CPP FILES ###     
from profiles.cpp_patterns import detect_cpp_patterns
              
def extract_cpp_hints(cpp_code: str) -> str:
    hints = detect_cpp_patterns(cpp_code)
    return " ".join(hints) if hints else ""



###############
### GENERAL ###                    
###############

def start_worker():
    while True:
        try:
            connection = connect_to_rabbitmq()
            channel = connection.channel()
            channel.queue_declare(queue="translation_queue", durable=True)

            def callback(ch, method, properties, body):
                try:
                    message = json.loads(body.decode())
                    file_id = message["file_id"]
                    original_filename = message["filename"]
                except Exception as parse_err:
                    logging.error(f"Failed to parse message: {body.decode()} — {parse_err}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                logging.info(f"Received job: file_id={file_id}, filename={original_filename}")
                time.sleep(3)
                translate_code(file_id, original_filename)
                logging.info(f"Completed job for {original_filename}. ACK sent.")
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue="translation_queue", on_message_callback=callback)
            logging.info("Worker is waiting for tasks...")
            channel.start_consuming()

        except pika.exceptions.ConnectionClosedByBroker:
            logging.warning("Connection closed by RabbitMQ. Retrying in 5s...")
            time.sleep(5)
        except Exception as e:
            logging.exception(f"Unexpected error. Restarting worker in 5s...")
            time.sleep(5)

if __name__ == "__main__":
    start_worker()
