# Use the NVIDIA CUDA base image with the full toolkit (devel)
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

FROM python:3.11-slim

WORKDIR /app

COPY ../requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/server.py .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
