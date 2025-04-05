######################################################################
### Worker that automatically generates JUnit tests for Java files ###
######################################################################

import pika
import json
import logging
import requests
import re
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Environment variables from .env
MODEL_NAME = os.getenv("LLM_MODEL")
SYSTEM_PROMPT = os.getenv("TEST_SYSTEM_PROMPT")
OLLAMA_URL = "http://ollama:11434/api/generate"
TESTS_DIR = "/test_worker/tests/"

# Ensure the directory for tests exists
os.makedirs(TESTS_DIR, exist_ok=True)

def generate_integration_test(java_file, cpp_test_reference=None):
    """
    Function to send a request to the LLM to generate a JUnit test for the provided Java file.
    """
    pascal_case_name = java_file.replace(".java", "")
    temp_test_file_path = os.path.join(TESTS_DIR, f"{pascal_case_name}Test.java")

    # Read the content of the Java file
    with open(java_file, "r") as file:
        java_code = file.read()

    ## If a C++ test reference is provided, include it in the prompt
    cpp_test_snippet = ""
    if cpp_test_reference:
        logging.info("C++ test reference provided. Including it in the prompt.")
        cpp_test_snippet = (
            "This shows how the original class was tested in C++. Preserve the testing logic and make the same number of tests and cases\n"
            "\n\n===== REFERENCE C++ TEST FILE =====\n"
            f"{cpp_test_reference.strip()}"
        )
    else:
        logging.info("No C++ test reference provided.")
        
    prompt = (
        f"Please generate a JUnit 5 test class for the following Java code. "
        f"The test should cover all public methods and reflect the logic and edge cases demonstrated in the C++ test.\n\n"
        f"===== JAVA CODE =====\n{java_code.strip()}\n\n"
        f"{cpp_test_snippet}\n\n"
        f"Instructions:\n"
        f"- Recreate the test logic and intent shown in the C++ test using idiomatic Java and JUnit 5.\n"
        f"- The resulting Java test class must be named exactly '{pascal_case_name}Test'.\n"
        f"- Instantiate any classes unless their methods are declared static.\n"
        f"- Do not assume static access unless explicitly declared.\n"
        f"- Use assertions from JUnit 5, such as assertEquals, assertTrue, assertFalse, and assertThrows.\n"
        f"- Make sure to include all necessary import statements, especially for classes from java.util.*, java.time.*, and java.time.format.*.\n"
        f"- If any CLI-like methods (e.g. main) are tested, test their logic via a helper method if possible.\n"
        f"- Return only the complete Java test class, including import statements. Do not include any explanations or external comments."
    )

    # Create a prompt for LLM to generate a JUnit test
    payload = {
        "model": MODEL_NAME,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "options": {            
                "num_ctx": 4000        # max context window size, default 2048 tokens, qwen2.5-coder limit 32,768
        },
        "stream": False
    }

    try:
        # Send the request to the LLM (Ollama)
        logging.info(f"Sending request to Ollama to generate JUnit test for {java_file}")
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()

        # Extract the generated Java test code from the LLM response
        response_json = response.json()
        generated_test_code = response_json.get("response", "").strip()

        #######################
        ### POST PROCESSING ###
        #######################
        
        # Extract only the Java code from the response
        retry_match = re.search(r"```(?:java)?\s*(.*?)```", generated_test_code, re.DOTALL)
        if retry_match:
            java_test_code = retry_match.group(1).strip()
        else:
            java_test_code = generated_test_code  # If no match, use the entire response
        
        # Save the processed Java test code into a test file
        with open(temp_test_file_path, "w") as output_file:
            output_file.write(java_test_code)

        logging.info(f"Generated test file saved to {temp_test_file_path}")
        return temp_test_file_path
    except Exception as e:
        logging.error(f"Error generating test for {java_file}: {e}")
        return None


def start_test_worker():
    """
    Worker function to listen for messages from RabbitMQ and generate tests for Java files.
    """
    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()

        # Declare the queue that will receive messages
        channel.queue_declare(queue='test_generation_queue', durable=True)

        def callback(ch, method, properties, body):
            """
            Callback function to process the message from the Translation Worker.
            """
            try:
                # Parse the incoming message
                message = json.loads(body.decode())
                action = message.get('action')

                if action == 'generate_test':
                    java_file = message.get('java_file_path')
                    cpp_test_reference = message.get('cpp_test_reference')
                    if java_file:
                        logging.info(f"Received request to generate test for: {java_file}")
                        test_file = generate_integration_test(java_file, cpp_test_reference)
                        if test_file:
                            logging.info(f"Generated test file: {test_file}")
                        else:
                            logging.warning(f"Failed to generate test for {java_file}")
                    else:
                        logging.warning(f"No Java file provided in the message.")

                else:
                    logging.warning(f"Unknown action: {action}")

                # Acknowledge the message after processing
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                logging.error(f"Error processing message: {e}")
                ch.basic_ack(delivery_tag=method.delivery_tag)

        # Start consuming messages from the queue
        logging.info("Test Generation Worker is waiting for tasks...")
        channel.basic_consume(queue='test_generation_queue', on_message_callback=callback)
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError:
        logging.warning("Connection to RabbitMQ lost. Retrying...")
        time.sleep(5)

if __name__ == "__main__":
    start_test_worker()
