import os
import requests
from dotenv import load_dotenv

load_dotenv()

def call_llm(messages, model="openai/gpt-3.5-turbo"):
    """
    Makes a request to the OpenRouter API.
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
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
