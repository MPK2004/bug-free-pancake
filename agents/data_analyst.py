import os
import re
import sys
import uuid
import time
from llm.client import call_llm

NAME = "Data Analyst"

DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
def redact(s: str) -> str:
    """Masks API keys, Auth headers, cookies, and strips PII/Credentialed URLs."""
    if not isinstance(s, str):
        return s
    s = re.sub('(sk-[A-Za-z0-9]{20,})', '****', s)
    s = re.sub('(Authorization:?\\s*Bearer\\s+)[A-Za-z0-9\\-\\._~+/]+=*', '\\1****', s, flags=re.IGNORECASE)
    s = re.sub('(Cookie:?\\s*)[^(\\s|;)]+', '\\1****', s, flags=re.IGNORECASE)
    s = re.sub('(https?://\\S+?)\\?.*?(?=\\s|$)', '\\1', s)
    return s

def analyze(context: dict):
    """
    Analytical Reasoning Layer: Data summary and ranking without artificial scoring.
    Used for lookup queries (e.g., "Top categories", "Sales by mall").
    """
    start_time = time.monotonic()
    user_query = context.get('user_query')
    raw_data = context.get('data', [])
    request_id = context.get('request_id') or str(uuid.uuid4())

    if not raw_data:
        return {'status': 'success', 'insights': ['No data found to aggregate.'], 'meta': {'rows_used': 0}}

    # Clean and round numeric values in the data for better presentation
    cleaned_data = []
    for row in raw_data:
        new_row = {}
        for k, v in row.items():
            if isinstance(v, float):
                new_row[k] = round(v, 2)
            else:
                new_row[k] = v
        cleaned_data.append(new_row)

    # Format data for LLM
    data_summary = "\n".join([str(row) for row in cleaned_data[:20]])
    
    analysis_prompt = f"""
Analyze the provided dataset to answer the user's analytical question. 

User Question: {user_query}

DATASET:
{data_summary}

STRICT RED LINES:
- Do NOT perform strategic scoring or mathematical normalization.
- Do NOT mention "risk", "yield", or "defensive match".
- Do NOT provide "recommendations" or "strategic fits".
- Focus purely on data patterns, rankings, and observations.

REASONING RULES:
1. Dominance Rule: Dominance is defined ONLY by the highest physical volume/demand (e.g., total sales). 
2. Priority Warning: The "priority" field (HIGH/MEDIUM/LOW) is a strategic goal, NOT a measure of current dominance.
3. Top-N Storytelling: If applicable, list the top candidates to provide better context (e.g., Top 3 categories).
4. Formatting: Use the headers below EXACTLY. Do NOT add your own numbering like "1. 1." or "1.".

OUTPUT FORMAT:
OBSERVATION:
(List key findings and raw numbers here)

INSIGHT:
(What the data implies about the market)

CONCLUSION:
(Direct answer to the user's query)
"""
    return _execute_llm_analysis(analysis_prompt, start_time, request_id, len(raw_data))

def _execute_llm_analysis(prompt, start_time, request_id, rows_count):
    if DEBUG:
        print(f'--- Executing Data Analyst (Analytical Mode) ---', file=sys.stderr)
        print(redact(prompt), file=sys.stderr)

    try:
        response = call_llm([{'role': 'user', 'content': prompt}], timeout=20)
        insights = [line.strip() for line in response.split('\n') if line.strip()]
        
        meta = {
            'request_id': request_id,
            'rows_used': rows_count,
            'duration_ms': int((time.monotonic() - start_time) * 1000)
        }

        return {'status': 'success', 'insights': insights, 'meta': meta}
    except Exception as e:
        print(f"Data Analyst LLM Error: {e}", file=sys.stderr)
        return {'status': 'error', 'message': 'Analytical analysis failed.', 'meta': {'request_id': request_id}}