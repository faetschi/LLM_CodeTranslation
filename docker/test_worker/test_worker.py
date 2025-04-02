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
OLLAMA_URL = "http://ollama:11434/api/generate"
TESTS_DIR = "/test_worker/tests/"

# Ensure the directory for tests exists
os.makedirs(TESTS_DIR, exist_ok=True)

def generate_integration_test(java_file):
    """
    Function to send a request to the LLM to generate a JUnit test for the provided Java file.
    """
    pascal_case_name = java_file.replace(".java", "")
    temp_test_file_path = os.path.join(TESTS_DIR, f"{pascal_case_name}Test.java")

    # Read the content of the Java file
    with open(java_file, "r") as file:
        java_code = file.read()

    # Create a prompt for LLM to generate a JUnit test
    payload = {
        "model": MODEL_NAME,
        "system": "You are a software engineer that generates JUnit test files for Java classes.",
        "prompt": (
            f"Please generate a JUnit 5 integration test for the following Java class. "
            f"The test should cover its public methods and should include a few edge cases.\n\n"
            f"===== JAVA CODE =====\n{java_code}\n\n"
            f"Please write only the JUnit test class, including necessary imports. The main class name should be exactly named {pascal_case_name}Test. "
            f"Don't include the original Java class or any explanation."
        ),
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
                    if java_file:
                        logging.info(f"Received request to generate test for: {java_file}")
                        test_file = generate_integration_test(java_file)
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
