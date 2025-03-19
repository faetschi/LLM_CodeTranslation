# Use the NVIDIA CUDA base image with the full toolkit (devel)
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

FROM python:3.11-slim

WORKDIR /worker

COPY ../requirements.txt .

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir -r requirements.txt

COPY worker/worker.py .

# -u for unbuffered output
CMD ["python", "-u", "worker.py"]