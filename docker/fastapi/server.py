from fastapi import FastAPI, UploadFile, File, Form
from typing import List, Optional
import uuid
import pika
import shutil
import os
import json

fastapi = FastAPI()

UPLOAD_DIR = "/fastapi/uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

RABBITMQ_HOST = 'rabbitmq'
TRANSLATION_QUEUE = 'translation_queue'

def send_to_queue(file_id, cpp_filename, custom_prompt=None, header_files=None):
    """
    Send translation job with full context to RabbitMQ.
    Includes file_id, file name, optional prompt, and full header content.
    """
    try:
        print(f"🔄  Connecting to {RABBITMQ_HOST} to send job {file_id}...")

        parameters = pika.ConnectionParameters(host=RABBITMQ_HOST)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.queue_declare(queue="translation_queue", durable=True, auto_delete=False)

        # Read the content of header files and include them in the message
        headers_payload = {}
        if header_files:
            for filename, filepath in header_files.items():
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        headers_payload[filename] = f.read()
                except Exception as e:
                    print(f"⚠️ Warning: Failed to read {filename}: {e}")

        job = {
            "file_id": file_id,
            "cpp_filename": cpp_filename,
            "custom_prompt": custom_prompt,
            "headers": headers_payload
        }

        channel.basic_publish(
            exchange="",
            routing_key=TRANSLATION_QUEUE,
            body=json.dumps(job),
            properties=pika.BasicProperties(delivery_mode=2),
        )

        print(f"✅ Sent job {file_id} to RabbitMQ")
        connection.close()

    except pika.exceptions.AMQPConnectionError as e:
        print(f"❌ ERROR: RabbitMQ connection failed: {str(e)}")
    except Exception as e:
        print(f"❌ ERROR: Failed to send job {file_id} to RabbitMQ: {str(e)}")

@fastapi.post("/translate/")
async def translate_file(
    files: List[UploadFile] = File(...),
    custom_prompt: Optional[str] = Form(None)
):
    """
    Receives a list of files (.cpp and .h), stores them,
    and sends metadata to the translation worker.
    """
    file_id = str(uuid.uuid4())
    uploaded_file_map = {}
    cpp_filename = None

    for file in files:
        save_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded_file_map[file.filename] = save_path

        if file.filename.endswith(".cpp"):
            cpp_filename = file.filename

    if not cpp_filename:
        return {"error": "No .cpp file found in upload. Please include one."}

    # Filter out .h files for header content
    headers = {
        name: path for name, path in uploaded_file_map.items()
        if name.endswith(".h")
    }

    send_to_queue(
        file_id=file_id,
        cpp_filename=cpp_filename,
        custom_prompt=custom_prompt,
        header_files=headers
    )

    return {
        "message": "Translation started",
        "file_id": file_id,
        "cpp_filename": cpp_filename,
        "headers_sent": list(headers.keys()),
        "custom_prompt": custom_prompt
    }
