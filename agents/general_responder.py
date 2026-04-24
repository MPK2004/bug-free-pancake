import os
import uuid
import time
from llm.client import call_llm

NAME = "General Responder"

def analyze(context: dict):
    """
    General Responder: Handles non-data queries like greetings, general knowledge, or system explanations.
    """
    start_time = time.monotonic()
    query = context.get('query')
    request_id = context.get('request_id') or str(uuid.uuid4())

    system_prompt = """
You are a helpful assistant for the Mall Leasing AI system. 
You provide direct, concise answers to general questions that do not require database lookups or financial calculations.
If the user asks something that seems like it might need data, but you were routed here, answer as best as you can without hallucinating specific database values.
"""

    try:
        response = call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ])
        
        insights = [line.strip() for line in response.split('\n') if line.strip()]
        
        meta = {
            'request_id': request_id,
            'duration_ms': int((time.monotonic() - start_time) * 1000)
        }

        return {'status': 'success', 'insights': insights, 'meta': meta}
    except Exception as e:
        return {
            'status': 'error', 
            'message': 'General response failed.', 
            'code': 'AGENT_ERROR',
            'meta': {'request_id': request_id, 'details': str(e)}
        }
