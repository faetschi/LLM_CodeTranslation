import os
import requests
import time
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL = os.getenv("LLM_MODEL")

def wait_for_ollama(max_attempts=60):
    for attempt in range(max_attempts):
        try:
            res = requests.get(f"{OLLAMA_URL}/", timeout=2)
            if res.status_code == 200:
                logging.info("Ollama is ready.")
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    logging.error("Ollama failed to start in time.")
    return False

def warm_model():
    logging.info(f"Sending preload request for model '{MODEL}'...")
    try:
        with requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL, "prompt": "say ready", "stream": True},
            stream=True,
            timeout=None
        ) as response:
            if response.status_code == 200:
                logging.info("Waiting for model to finish loading tensors...")
                logging.info(f"Model '{MODEL}' is now loaded into memory.")
            else:
                logging.error(f"Failed to preload model: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error preloading model: {e}")

if __name__ == "__main__":
    if wait_for_ollama():
        warm_model()
