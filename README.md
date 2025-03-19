# Prototype for Code Translation with Large Language Models using Ollama

🚀 Fast 
💡 Modular 
📈 Scalable

Docker for Deployment

## Architecture

[ User/API Request ]
       ↓
[ FastAPI Service ]  → Handles authentication, rate limiting, and API requests (users upload C++ files)
       ↓
[ Task Queue (RabbitMQ)]  → Distributes tasks across multiple workers, depending on GPU availability (for now, 1 worker, 1 GPU)
       ↓
[ Translation Worker (Ollama)]  → Uses GPU efficiently to translate C++ to Java
       ↓
[ Storage (Local)] → Saves translated Java files (prototype: local storage, future: cloud storage)
       ↓
[ API Response ] → Returns translated Java file


## Docker Commands

docker exec -it ollama sh

       ollama list

       curl -s -X POST -H "Content-Type: application/json" \
     --data '{"model": "qwen2.5-coder:7b", "pr> ompt": "What is 1 + 1?", "stream": false}' \
     > http://localhost:11434/api/generate | grep -o '"response":"[^"]*"' | sed 's/"response":"//;s/"$//'
       

docker logs translation_worker --follow



## Steps to Implement the Prototype

Set up Docker with FastAPI, RabbitMQ, and Ollama.
Implement the FastAPI service to handle file uploads & retrieval.
Set up RabbitMQ and make sure messages are correctly queued.
Develop a Python worker to process translations using Ollama.
Test the prototype with sample C++ files.
Implement logging & basic error handling.
Prepare documentation for scalability & future improvements.


- Set Up FastAPI for User Requests
Users upload C++ files via an API.
API validates input, assigns a unique file ID, and stores the file temporarily.
Sends a task to RabbitMQ for processing.

- Implement Task Queue (RabbitMQ)
FastAPI sends file IDs to RabbitMQ.
RabbitMQ manages job distribution (for now, just 1 worker, later can scale to multiple GPUs).

- Develop Translation Worker
Worker fetches the job from RabbitMQ.
Reads the C++ file, sends it to Ollama for translation.
Saves the translated Java file locally.

- Store Translated Files
Saves Java files in a local directory (future: S3 storage for cloud access).

Files can be retrieved via API.
- Return API Response
User requests translated file using the unique file ID.
API checks storage and returns the Java file.