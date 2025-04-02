FROM python:3.11-slim
WORKDIR /app
COPY model_loader/ping.py .
RUN pip install requests
CMD ["python", "ping.py"]
