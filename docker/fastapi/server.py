from fastapi import FastAPI, UploadFile, File
import pika
import uuid
import shutil
import os
import json

fastapi = FastAPI()

UPLOAD_DIR = "/fastapi/uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def send_to_queue(file_id, original_filename):
    """Send the job (file_id + filename) to RabbitMQ."""
    try:
        print(f"🔄  Connecting to RabbitMQ to send job {file_id}...")

        parameters = pika.ConnectionParameters(host='rabbitmq')
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.queue_declare(queue="translation_queue", durable=True, auto_delete=False)

        # Create the job message
        job = {
            "file_id": file_id,
            "filename": original_filename
        }

        channel.basic_publish(
            exchange="",
            routing_key="translation_queue",
            body=json.dumps(job),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent message
            ),
        )

        print(f"✅  Sent job {job} to RabbitMQ")
        connection.close()

    except pika.exceptions.AMQPConnectionError as e:
        print(f"❌  ERROR: RabbitMQ connection failed: {str(e)}")
    except Exception as e:
        print(f"❌  ERROR: Failed to send job {file_id} to RabbitMQ: {str(e)}")

@fastapi.post("/translate/")
async def translate_file(file: UploadFile = File(...)):
    """Handles file upload & immediately sends task to RabbitMQ."""

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.cpp")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"✅ Uploaded file: {file_path}")

    # Send file_id + original filename to queue
    send_to_queue(file_id, file.filename)

    return {
        "message": "Translation started",
        "file_id": file_id,
        "original_filename": file.filename
    }
