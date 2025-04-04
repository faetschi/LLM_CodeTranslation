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

# Install JUnit 5 Libraries
ENV JUNIT_JUPITER_VERSION=5.8.1
ENV JUNIT_PLATFORM_VERSION=1.8.1
ENV OPENTEST4J_VERSION=1.2.0
ENV APIGUARDIAN_VERSION=1.1.2
ENV JUNIT_LIB_DIR_PATH=/app/libs

# Create the directory and download JUnit JARs needed for compilation
RUN mkdir -p ${JUNIT_LIB_DIR_PATH} && \
    cd ${JUNIT_LIB_DIR_PATH} && \
    echo "Downloading JUnit JARs to ${JUNIT_LIB_DIR_PATH}..." && \
    wget https://repo1.maven.org/maven2/org/junit/jupiter/junit-jupiter-api/${JUNIT_JUPITER_VERSION}/junit-jupiter-api-${JUNIT_JUPITER_VERSION}.jar && \
    wget https://repo1.maven.org/maven2/org/junit/jupiter/junit-jupiter-params/${JUNIT_JUPITER_VERSION}/junit-jupiter-params-${JUNIT_JUPITER_VERSION}.jar && \
    wget https://repo1.maven.org/maven2/org/junit/platform/junit-platform-commons/${JUNIT_PLATFORM_VERSION}/junit-platform-commons-${JUNIT_PLATFORM_VERSION}.jar && \
    wget https://repo1.maven.org/maven2/org/opentest4j/opentest4j/${OPENTEST4J_VERSION}/opentest4j-${OPENTEST4J_VERSION}.jar && \
    wget https://repo1.maven.org/maven2/org/apiguardian/apiguardian-api/${APIGUARDIAN_VERSION}/apiguardian-api-${APIGUARDIAN_VERSION}.jar && \
    echo "Finished downloading JUnit JARs." && \
    cd /test_worker # Return to workdir

# Set Default JUNIT_LIB_DIR Env Var
ENV JUNIT_LIB_DIR=${JUNIT_LIB_DIR_PATH}

# Install necessary Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the test worker
COPY test_worker/test_worker.py .

# Run the worker
CMD ["python", "-u", "test_worker.py"]
