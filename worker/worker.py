import os
import time
import requests
import pika

UPLOAD_DIR = "/app/uploads/"
TRANSLATED_DIR = "/app/translated/"
OLLAMA_URL = "http://ollama:11434/api/generate"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TRANSLATED_DIR, exist_ok=True)

def connect_to_rabbitmq():
    """Attempts to connect to RabbitMQ, retrying if necessary."""
    retries = 5
    for i in range(retries):
        try:
            print("🔄 Connecting to RabbitMQ...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            print("✅ Connected to RabbitMQ!")
            return connection
        except pika.exceptions.AMQPConnectionError:
            print(f"❌ RabbitMQ not available. Retrying {i+1}/{retries}...")
            time.sleep(5)
    raise Exception("❌ Failed to connect to RabbitMQ after multiple retries.")

def translate_code(file_id):
    """Fetches the C++ file, translates it via Ollama, and saves output."""
    
    cpp_file_path = os.path.join(UPLOAD_DIR, f"{file_id}.cpp")
    java_file_path = os.path.join(TRANSLATED_DIR, f"{file_id}.java")

    if not os.path.exists(cpp_file_path):
        print(f"❌ ERROR: File {cpp_file_path} not found!")
        return

######## TODO
# Implement that the file is correctly read 
# and appended to the prompt in format that LLM understands
    with open(cpp_file_path, "r") as file:
        cpp_code = file.read()

    payload = {
        "model": "qwen2.5-coder:7b", 
        "prompt": f"Translate this C++ code to Java:\n\n{cpp_code}",
        #"prompt": f"What is 1 + 1?",
        "stream": False  # Ensure Ollama returns a single response
    }

    try:
        print(f"🌐 Sending request to Ollama: {OLLAMA_URL} with model '{payload['model']}'", flush=True)
        
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()  # This will trigger an error if the request fails

        # Log the full response for debugging
        response_json = response.json()
        print(f"📥 Ollama Response: {response_json}", flush=True)
        
        translated_text = response_json.get("response", "Translation failed")
        
        if translated_text.strip() == "":
            print(f"⚠️ WARNING: Empty translation response for {file_id}", flush=True)
            return
        print(f"📥 Translation: {translated_text}", flush=True)
        

        # Extract response text
        java_code = response_json.get("response", "Translation failed")

        # Ensure we don't save an empty response
        if java_code.strip() == "":
            print(f"⚠️ WARNING: Empty translation response for {file_id}", flush=True)
            return

        # Save the translated Java file
        # TODO make sure response is correctly saved as new java file to the java_file_path
        with open(java_file_path, "w") as output_file:
            output_file.write(translated_text)

        print(f"✅ Translated {file_id} successfully. Output saved to {java_file_path}", flush=True)

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP ERROR {http_err.response.status_code}: {http_err.response.text}", flush=True)
    except Exception as e:
        print(f"❌ ERROR: Failed to translate {file_id}: {e}", flush=True)


def start_worker():
    """Continuously listens to 'translation_queue' for file IDs to translate."""
    while True:
        try:
            connection = connect_to_rabbitmq()
            channel = connection.channel()
            channel.queue_declare(queue="translation_queue", durable=True)

            def callback(ch, method, properties, body):
                file_id = body.decode()
                print(f"🔄 Received job for file_id: {file_id}")

                # A small optional delay (e.g. 2s) before processing
                time.sleep(2)

                # Perform the translation
                translate_code(file_id)

                # Acknowledge that we've processed the job
                print(f"✅ Completed job for file_id: {file_id}, sending ACK.")
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(
                queue="translation_queue",
                on_message_callback=callback
            )

            print("🚀 Worker is waiting for tasks...")
            channel.start_consuming()

        except pika.exceptions.ConnectionClosedByBroker:
            print("❌ Connection closed by RabbitMQ. Retrying in 5s...")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Unexpected error: {e}. Restarting worker in 5s...")
            time.sleep(5)

if __name__ == "__main__":
    start_worker()
