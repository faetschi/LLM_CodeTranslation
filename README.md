# Prototype for Code Translation with Large Language Models using Ollama

This project is a **prototype system** that uses **LLMs (via Ollama)** to automatically translate C++ code into Java. 
It is designed to be **modular** and **scalable**, using Docker and message queues to coordinate services and acting as a **proof-of-concept** for future enterprise adaptation.

# Technologies Used
- `Python` (FastAPI, pika, requests)
- `Docker`
- `FastAPI` (file upload & job dispatch)
- `RabbitMQ` (message queue)
- `Ollama` (LLM deployment)

## 🔧 Components

### 1. FastAPI Service
- Exposes an HTTP API (`/translate/`)
- Accepts `.cpp` file uploads
- Sends the `file_id` to RabbitMQ for translation
- Saves files to `/app/uploads/`

### 2. RabbitMQ
- Acts as a **message broker**
- Holds queued translation jobs (`file_id`) until a worker is ready
- Enables decoupling of the upload and translation process

### 3. Worker Service
- Written in Python
- Listens to RabbitMQ for translation jobs
- For each `file_id`:
  - Reads the corresponding `.cpp` file
  - Applies Pre-Processing 
  - Sends it to the **Ollama LLM** with a prompt
  - Saves the translated output as `.java` to `/app/translated/`

### 4. Ollama (LLM)
- Uses the `qwen2.5-coder:7b` model
- Exposes an API at `http://ollama:11434/api/generate`
- Accepts code based natural language prompts


# How to use

Build with Docker

       docker compose build

Download the model you want to use

       docker exec -it ollama ollama pull qwen2.5-coder:7b

Set the used model name in .env

       LLM_MODEL=modelname
       e.g. LLM_MODEL=qwen2.5-coder:7b

Start services via docker

       docker compose up


Send file as POST Request using curl or Postman

       curl -X POST http://localhost:8000/translate/ \ -F "file=@test.cpp"


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

# WIP

Translation -> Temp File -> Java Compiler drüberlaufen lassen -> Code + Errors in LLM geben zur Validation -> Output File in translated folder -> Final java compiler drüber laufen lassen

## Docker Commands

docker compose up --build -d

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