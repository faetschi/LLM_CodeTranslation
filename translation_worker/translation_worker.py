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

UPLOAD_DIR = "/app/uploads/"
TEMP_DIR = "/app/temp/"
TRANSLATED_DIR = "/app/translated/"
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
    temp_java_file_path = os.path.join(TEMP_DIR, f"{pascal_case_name}.java")
    final_java_file_path = os.path.join(TRANSLATED_DIR, f"{pascal_case_name}.java")

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
            f'Translate the following complete C++ source file into clean Java 17. '
            f"===== C++ CODE =====\n"
            f"{cpp_code}\n\n"
            f'Ensure the structure is valid: all imports must be at the top, '
            f'helper classes and methods must be properly nested, and the code must form a valid Java 17 file.\n\n'
            f'The main public class must have the name "{pascal_case_name}" (the filename is "{pascal_case_name}" and the class name must match this name). '
            f'Do not output any public class named "Main".\n\n'
            f"These are hints found in the Java code:\n{cpp_hints}\n\n"
            f'Output only valid Java code.\n'
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

        with open(temp_java_file_path, "w") as output_file:
            output_file.write(java_code)

        logging.info(f"Initial translation saved to {temp_java_file_path}")
        success, compile_log = compile_java_file(temp_java_file_path)

        if success:
            shutil.copy(temp_java_file_path, final_java_file_path)
            logging.info(f"Compilation successful. File copied to {final_java_file_path}")
            
        #####################################
        ### RETRY PHASE AFTER COMPILATION ###                    
        #####################################
        else:
            logging.warning(f"Compilation failed. Attempting fix...")
            logging.info("Compile LOG: \n" + compile_log)
            sanitized_log = sanitize_log(compile_log)
            
            # Run PMD analysis to capture static analysis issues
            pmd_log = run_pmd_analysis(temp_java_file_path)
            logging.info("PMD LOG: \n" + pmd_log)
            
            retry_payload = {
                "model": MODEL_NAME,
                "system": SYSTEM_PROMPT,
                "prompt": (
                    f"The following Java code was generated from a C++ source file, but it fails to compile when saved as \"{pascal_case_name}.java\":\n\n"
                    f"===== JAVA CODE =====\n"
                    f"{java_code}\n\n"
                    f"===== COMPILATION ERRORS (first 50 lines) =====\n"
                    f"{sanitized_log}\n\n"
                    f"===== Static Analysis Issues =====\n"
                    f"{pmd_log}\n\n"
                    f"Please correct all the issues so that the code compiles as a valid Java 17 file. Address the following problems explicitly:\n"
                    f"1. The file contains exactly one public class, and its name is exactly \"{pascal_case_name}\" (do not output any public class named \"Main\").\n"
                    f"2. Resolve any symbol errors (for example, methods that are missing or incorrectly referenced).\n"
                    f"3. Adjust access modifiers so that methods meant to be called externally are declared public.\n"
                    f"4. Correct any invalid method declarations, ensure constructors or methods have the proper return types if required.\n\n"
                    f"The main public class must have the name \"{pascal_case_name}\" (the filename is \"{pascal_case_name}\" and the class name must match this name).\n"
                    f"Return only the corrected Java 17 code with no explanations, comments, or markdown formatting."
                ),
                "stream": False
            }

            retry_response = requests.post(OLLAMA_URL, json=retry_payload)
            retry_response.raise_for_status()
            retry_result = retry_response.json().get("response", "").strip()
            retry_match = re.search(r"```(?:java)?\s*(.*?)```", retry_result, re.DOTALL)
            
            #######################
            ### POST PROCESSING ###
            #######################
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
                cleanup_class_files(temp_java_file_path)
                cleanup_class_files(final_java_file_path)
            else:
                failed_path = final_java_file_path.replace(".java", "_failed.java")
                logging.error(f"Retry failed again. Output saved to {failed_path}\n{retry_log}")
                ### CLEAN temp files ###
                cleanup_class_files(temp_java_file_path)
                cleanup_class_files(final_java_file_path)
                
            try:
                if os.path.exists(cpp_file_path):
                    os.remove(cpp_file_path)
                    logging.info(f"🧹 Removed original .cpp file: {os.path.basename(cpp_file_path)}")
            except Exception as e:
                logging.warning(f"⚠️ Could not remove original .cpp file: {cpp_file_path} — {e}")


    except Exception as e:
        logging.exception(f"Exception while translating {file_id}: {e}")
        
        
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
            
        
def cleanup_class_files(java_file_path):
    """Deletes any .class files generated by javac in the file's directory,
       in TEMP_DIR, and in TRANSLATED_DIR.
       Also, deletes the .java file if it's in TEMP_DIR.
    """
    base_path = os.path.splitext(java_file_path)[0]
    dir_path = os.path.dirname(java_file_path)
    
    # Delete .class files in the same directory as the java_file_path.
    for filename in os.listdir(dir_path):
        if filename.startswith(os.path.basename(base_path)) and filename.endswith(".class"):
            try:
                os.remove(os.path.join(dir_path, filename))
                logging.info(f"Removed leftover class file: {filename}")
            except Exception as e:
                logging.warning(f"Could not remove class file {filename}: {e}")
                
    # Delete .class files in TEMP_DIR and TRANSLATED_DIR.
    for directory in [TEMP_DIR, TRANSLATED_DIR]:
        for filename in os.listdir(directory):
            if filename.endswith(".class"):
                try:
                    os.remove(os.path.join(directory, filename))
                    logging.info(f"Removed temporary class file from {directory}: {filename}")
                except Exception as e:
                    logging.warning(f"Could not remove temporary class file {filename} from {directory}: {e}")

    # Only delete the .java file if it's in TEMP_DIR.
    if TEMP_DIR in java_file_path:
        try:
            if os.path.exists(java_file_path):
                os.remove(java_file_path)
                logging.info(f"Removed temporary Java file: {os.path.basename(java_file_path)}")
        except Exception as e:
            logging.warning(f"Could not remove temporary Java file: {java_file_path} — {e}")
            
            
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

def extract_cpp_hints(cpp_code: str) -> str:
    hints = []
    
    # Extract class names
    classes = re.findall(r'\bclass\s+(\w+)', cpp_code)
    if classes:
        hints.append(f"Found C++ classes: {', '.join(classes)}.")
    
    # Extract namespace declarations
    namespaces = re.findall(r'\bnamespace\s+(\w+)', cpp_code)
    if namespaces:
        hints.append(f"Found namespaces: {', '.join(namespaces)}.")
    
    # Detect template usage for conversion to Java generics
    if re.search(r'\btemplate\s*<', cpp_code):
        hints.append("Found template usage. Translate to Java generics.")
    
    # Detect pointer declarations (avoid false positives with multiplication by using word boundaries)
    if re.search(r'\b\w+\s*\*', cpp_code):
        hints.append("Found pointer declarations. Replace with Java object references.")
    
    # Detect usage of new and delete (indicating dynamic memory management)
    if re.search(r'\b(new|delete)\b', cpp_code):
        hints.append("Found dynamic memory management using new/delete. Use Java's garbage collection instead.")
    
    # Check for common STL container usage (vector, map, etc.)
    stl_containers = []
    if re.search(r'\bvector<', cpp_code):
        stl_containers.append("vector")
    if re.search(r'\bmap<', cpp_code):
        stl_containers.append("map")
    if stl_containers:
        hints.append(f"Found STL container usage: {', '.join(stl_containers)}. Map these to Java Collections.")
    
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
