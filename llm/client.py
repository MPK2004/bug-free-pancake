import os
import requests
from dotenv import load_dotenv
load_dotenv()

class LLMError(Exception):

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

class LLMAuthError(LLMError):
    pass

class LLMRateLimitError(LLMError):
    pass

class LLMOverloadError(LLMError):
    pass

def call_llm(messages, model='openai/gpt-3.5-turbo', timeout=None, tools=None, raw=False):
    # Maintain raw=False as default; existing agents (data_analyst.py, decision_engine.py)
    # expect a plain string response. raw=True is for tool-calling agents.
    url = 'https://openrouter.ai/api/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {os.getenv("OPENROUTER_API_KEY")}', 
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/MPK2004/bug-free-pancake', # Good practice for OpenRouter
        'X-Title': 'Financial Analyst Agent'
    }
    
    data = {'model': model, 'messages': messages}
    if tools:
        data['tools'] = tools
        
    try:
        env_timeout = int(os.getenv('LLM_TIMEOUT', '15'))
    except (TypeError, ValueError):
        env_timeout = 15
    final_timeout = max(1.0, float(timeout if timeout is not None else env_timeout))

    import re
    def _redact_url(msg):
        return re.sub('(https?://\\S+?)\\?.*?(?=\\s|$)', '\\1', msg)
        
    try:
        response = requests.post(url, headers=headers, json=data, timeout=final_timeout)
        if response.status_code == 401:
            raise LLMAuthError('Authentication failed. Please check OpenRouter API key.', status_code=401)
        elif response.status_code == 429:
            raise LLMRateLimitError('Rate limit exceeded (429).', status_code=429)
        elif response.status_code in [503, 504]:
            raise LLMOverloadError(f'Service unavailable ({response.status_code}).', status_code=response.status_code)
        response.raise_for_status()
        
        full_response = response.json()
        if raw:
            return full_response
        return full_response['choices'][0]['message'].get('content', '')
        
    except requests.exceptions.Timeout:
        raise LLMError('Request timed out.', status_code=408)
    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500
        raise LLMError(_redact_url(f'LLM request failed: {str(e)}'), status_code=status_code)