# Use the NVIDIA CUDA base image with the full toolkit (devel)
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /test_worker

# Copy requirements.txt into the container
COPY ../requirements.txt .

# Set Python to unbuffered output mode
ENV PYTHONUNBUFFERED=1

# Install Java 17, wget, unzip, and other required tools
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk curl wget unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install PMD for static analysis 
ENV PMD_VERSION=7.11.0
RUN wget https://github.com/pmd/pmd/releases/download/pmd_releases%2F${PMD_VERSION}/pmd-dist-${PMD_VERSION}-bin.zip && \
    unzip pmd-dist-${PMD_VERSION}-bin.zip && \
    rm pmd-dist-${PMD_VERSION}-bin.zip && \
    mv pmd-bin-${PMD_VERSION} /opt/pmd

# Add PMD to PATH
ENV PATH="/opt/pmd/bin:${PATH}"

# Install necessary Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the test worker
COPY test_worker/test_worker.py .

# Run the worker
CMD ["python", "-u", "test_worker.py"]
