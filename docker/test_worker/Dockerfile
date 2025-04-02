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
# Define versions (use recent stable versions)
ENV JUNIT_PLATFORM_VERSION=1.10.2
ENV JUNIT_JUPITER_VERSION=5.10.2
ENV JUNIT_LIB_DIR_PATH=/app/libs

# Create the directory and download JUnit JARs needed for compilation
RUN mkdir -p ${JUNIT_LIB_DIR_PATH} && \
    cd ${JUNIT_LIB_DIR_PATH} && \
    wget https://repo1.maven.org/maven2/org/junit/platform/junit-platform-commons/${JUNIT_PLATFORM_VERSION}/junit-platform-commons-${JUNIT_PLATFORM_VERSION}.jar && \
    wget https://repo1.maven.org/maven2/org/junit/jupiter/junit-jupiter-api/${JUNIT_JUPITER_VERSION}/junit-jupiter-api-${JUNIT_JUPITER_VERSION}.jar && \
    # Add other JUnit JARs if needed by generated tests (e.g., params, engine - though engine might only be needed for running)
    # wget https://repo1.maven.org/maven2/org/junit/jupiter/junit-jupiter-params/${JUNIT_JUPITER_VERSION}/junit-jupiter-params-${JUNIT_JUPITER_VERSION}.jar && \
    # wget https://repo1.maven.org/maven2/org/opentest4j/opentest4j/1.3.0/opentest4j-1.3.0.jar && \
    # wget https://repo1.maven.org/maven2/org/apiguardian/apiguardian-api/1.1.2/apiguardian-api-1.1.2.jar && \
    cd /test_worker # Return to workdir

# Set Default JUNIT_LIB_DIR Env Var
ENV JUNIT_LIB_DIR=${JUNIT_LIB_DIR_PATH}

# Install necessary Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the test worker
COPY test_worker/test_worker.py .

# Run the worker
CMD ["python", "-u", "test_worker.py"]
