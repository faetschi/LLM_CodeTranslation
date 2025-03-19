# Use the NVIDIA CUDA base image with the full toolkit (devel)
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

WORKDIR /app

FROM python:3.11-slim

# Copy requirements first for better caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]