FROM python:3.11-slim
WORKDIR /app
COPY ping.py .
RUN pip install requests
CMD ["python", "ping.py"]
