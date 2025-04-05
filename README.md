# Prototype for Code Translation with Large Language Models using Ollama

This project is a **prototype system** that uses **LLMs (via Ollama)** to automatically translate C++ code into Java. 
It is designed to be **modular** and **scalable**, using Docker and message queues to coordinate services and acting as a **proof-of-concept** for future enterprise adaptation.

## 🚀 Technologies Used

- `Python`
- `Docker` - Containerization of services
- [`FastAPI`](https://fastapi.tiangolo.com/) - REST APIs
- [`RabbitMQ`](https://www.rabbitmq.com/) - Message broker for decoupling and task queueing
- [`Ollama`](https://ollama.com/) -  Local LLM engine
- `javac`, `PMD` - Java compiler and static code analysis tool for validation

## 📦 How to Use

1. Build the containers

    ```bash
    docker compose build
    ```

2. Pull your preferred model

    ```bash
    docker exec -it ollama ollama pull qwen2.5-coder:7b
    ```

    Set the model in `.env`:

    ```bash
    LLM_MODEL=qwen2.5-coder:7b
    ```

3. Start all services

    ```bash
    docker compose up
    ```

4. Send a C++ file via `HTTP request`

    ```bash
    curl -X POST http://localhost:8000/translate/ \
      -F "file=@path/to/your/test.cpp"
    ```

## 🧱 System Architecture

<img src="./docs/svg/architecture.svg" alt="System Architecture" style="max-width: 100%; width: 60%; height: auto;" />

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

## Example POST-Request Parameter:

| Info| Key | Type | Value |
|---|-----|-----------|-------------|
| .cpp file | files | File | isValidTradingPair.cpp |
| .h file | files | File | c.datum.h
| .h file | files | File | c.waehrung.h
| *(optional)* test_ .cpp file |files | File | test_isValidTradingPair.cpp
| *(optional)*|custom_prompt | Text | The previous output missed a static nested helper class called Config. Ensure it’s static and public. |

## TODO Testing Documentation

### Existing files are overwritten when Request with same filename happens

- isValidTradingPair
  - Files:
    - isValidTradingPair.cpp
    - c_datum.h
    - c_waehrung.h
    - test_isValidTradingPair

First Iteration


Second Iteration

Added 2 lines at Auto generated Test: test_isValidTradingPair.java:

    import IsValidTradingPair.IsValidTradingPair.cADatum;
    import IsValidTradingPair.IsValidTradingPair.cWaehrung;

8/8 Tests successful.

| Input | Java Output | C++ Output | Note |
|--|--|--|--|
|-d20250419 -pEURUSD -v | 20250419 - Kein Handelstag <br> 0 | 20250419 - Kein Handelstag |
| -d20250403 -pEURUSD -v | 20250421 - Gueltiges Trading-Paar: EURUSD | 20250403 - Gueltiges Trading-Paar: EURUSD
| -d20250403 -pBADKURS -v | 20250403 - Kein Handelstag | 20250403 - Ungueltiges Waehrungspaar: BADKURS | WRONG EDGECASE






## 🛠 Debugging

- Helpful Docker Commands

  ```bash
  docker compose up --build -d              # detached mode
  docker logs translation_worker --follow   # show logs of service
  docker exec -it ollama sh
  ollama list                               # list available models
  ```

- Test LLM directly:

  ```bash
  curl -s -X POST http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{"model": "qwen2.5-coder:7b", "prompt": "What is 1 + 1?", "stream": false}'
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

