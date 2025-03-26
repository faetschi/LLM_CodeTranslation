# Use the NVIDIA CUDA base image with the full toolkit (devel)
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

FROM python:3.11-slim

WORKDIR /translation_worker

COPY ../requirements.txt .

ENV PYTHONUNBUFFERED=1

# Install Java 17 and other required tools
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install wordninja

RUN pip install stringcase

COPY translation_worker/translation_worker.py .

# -u for unbuffered output
CMD ["python", "-u", "translation_worker.py"]