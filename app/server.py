from fastapi import FastAPI, UploadFile, File
import pika
import uuid
import shutil
import os

app = FastAPI()

UPLOAD_DIR = "/app/uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def send_to_queue(file_id):
    """Send the job to RabbitMQ and confirm message delivery."""
    try:
        print(f"🔄  Connecting to RabbitMQ to send job {file_id}...")
        parameters = pika.ConnectionParameters(host='rabbitmq')
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Ensure queue is durable and survives restarts
        channel.queue_declare(queue="translation_queue", durable=True, auto_delete=False)

        # Send message as persistent
        channel.basic_publish(
            exchange="",
            routing_key="translation_queue",
            body=file_id,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent message
            ),
        )

        print(f"✅  Sent job {file_id} to RabbitMQ")

        # Check if message is actually stored
        method_frame, header_frame, body = channel.basic_get(queue="translation_queue")
        if method_frame:
            print(f"📦  Job is in the queue! Queue message count: {method_frame.message_count}")
        else:
            print("❌ ERROR: No message found in the queue after publishing!")

        connection.close()

    except pika.exceptions.AMQPConnectionError as e:
        print(f"❌  ERROR: RabbitMQ connection failed: {str(e)}")
    except Exception as e:
        print(f"❌  ERROR: Failed to send job {file_id} to RabbitMQ: {str(e)}")

@app.post("/translate/")
async def translate_file(file: UploadFile = File(...)):
    """Handles file upload & immediately sends task to RabbitMQ."""

    file_id = str(uuid.uuid4())  
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.cpp")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"✅ Uploaded file: {file_path}")

    # Immediately send job to RabbitMQ
    send_to_queue(file_id)
    
    return {"message": "Translation started", "file_id": file_id}
