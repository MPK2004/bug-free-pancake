import os
import requests
from dotenv import load_dotenv

load_dotenv()

def call_llm(messages, model="openai/gpt-3.5-turbo"):
    """
    Makes a request to the OpenRouter API with a configurable timeout.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": messages
    }
    
    # Configurable timeout with safe fallback
    try:
        timeout = int(os.getenv("LLM_TIMEOUT", "15"))
    except (TypeError, ValueError):
        timeout = 15

    response = requests.post(url, headers=headers, json=data, timeout=timeout)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
