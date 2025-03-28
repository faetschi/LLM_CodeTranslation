# Prototype for Code Translation with Large Language Models using Ollama

This project is a **prototype system** that uses **LLMs (via Ollama)** to automatically translate C++ code into Java. 
It is designed to be **modular** and **scalable**, using Docker and message queues to coordinate services and acting as a **proof-of-concept** for future enterprise adaptation.

## 🚀 Technologies Used

- `Python`
- `Docker`
- [`FastAPI`](https://fastapi.tiangolo.com/)
- [`RabbitMQ`](https://www.rabbitmq.com/)
- [`Ollama`](https://ollama.com/)
- `javac`, `PMD`

## 🔧 Components

### **FastAPI Service (Frontend Interface)**
- Exposes an HTTP API at `/translate/`
- Accepts `.cpp` file uploads
- Stores uploaded files in `/fastapi/uploads/`
- Sends jobs (file ID + metadata) to RabbitMQ

### **RabbitMQ (Task Queue / Message Broker)**
- Holds queued translation jobs until a worker is ready
- Decouples frontend upload from backend processing
- Ensures reliable delivery of tasks

### **Translation Worker (Core Logic)**
- Written in Python
- Listens for tasks via RabbitMQ
- Handles full translation pipeline:
  - Preprocessing of C++ input
  - Prompt-based translation using LLM
  - Compilation with `javac`
  - Retry logic using error feedback + PMD analysis
  - Final Java files saved in `/translation_worker/translated/`

### **Ollama (LLM Engine)**
- Hosts the selected model (e.g., `qwen2.5-coder:7b`)
- Receives structured prompts via `POST /api/generate`
- Returns Java code translations
- Can be swapped with other LLMs that support local inference


## 📦 How to Use

### 1. **Build the containers**

```bash
docker compose build
```

### 2. **Pull your preferred model**

```bash
docker exec -it ollama ollama pull qwen2.5-coder:7b
```
**Set the model in `.env`:**

```bash
LLM_MODEL=qwen2.5-coder:7b
```

### 3. **Start all services**

```bash
docker compose up
```

### 4. **Send a C++ file via HTTP request**

```bash
curl -X POST http://localhost:8000/translate/ \
  -F "file=@path/to/your/test.cpp"
```

## 🧱 System Architecture

```plaintext
[ User/API Request ]
       ↓
[ FastAPI Service ] 
   ├─ Receives .cpp file uploads
       ↓
[ RabbitMQ ]
   ├─ Queues file_id translation task
       ↓
[ Translation Worker ]
   ├─ Preprocess C++ + extract hints
   ├─ Send prompt to LLM (Ollama)
   ├─ Compile Java file
   ├─ Retry with compile + PMD feedback
   └─ Save final output in /translated/
       ↓
[ Java File Output ]

```

## 🛠 Helpful Docker Commands

```bash
docker compose up --build -d
docker logs translation_worker --follow
docker exec -it ollama sh
ollama list
```

Test LLM directly:

```bash
curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5-coder:7b", "prompt": "Translate this code...", "stream": false}'
```
       
## 📚 Future Improvements (WIP)

- Fine-tune LLMs on enterprise code

- Add integration tests for translated output

- Expand support for other language pairs

- Connect to PostgreSQL or cloud storage for outputs

- Add web UI for job monitoring

## 📄 License

This prototype is part of a **Bachelor Thesis project** by **Fabian Jelinek (2025)**, developed in cooperation with **Oesterreichische Kontrollbank AG (OeKB)**. 
It is intended for academic use and demonstration purposes.

This project is licensed under the [MIT License](LICENSE).  
© 2025 Fabian Jelinek. All rights reserved.

