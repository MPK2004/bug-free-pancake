import os
import re
import sys
import uuid
import time
import json
from llm.client import call_llm
from ai_system import TOOL_REGISTRY
from agents.tool_schemas import FINANCIAL_TOOLS

NAME = "Financial Analyst"

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
    Financial Analyst: Specialized in financial calculations via tool-calling loop.
    """
    start_time = time.monotonic()
    query = context.get('query')
    raw_data = context.get('data', [])
    request_id = context.get('request_id') or str(uuid.uuid4())
    
    # Early exit if no data is found to prevent LLM hallucination in tool-calling loop
    if not raw_data:
        return {
            'status': 'success', 
            'insights': ['No financial data found to analyze for this query.'], 
            'meta': {
                'request_id': request_id, 
                'rows_used': 0, 
                'duration_ms': int((time.monotonic() - start_time) * 1000)
            }
        }
    
    # We might need both proposals and tenants. 
    # If the SQL query was generic, we might have mixed data or just one type.
    # Structured data for prompt
    data_summary = json.dumps(raw_data[:20], indent=2)

    system_prompt = f"""
You are a Financial Analyst.

You are given:
1. A user query
2. A structured dataset (from a database)

The dataset is already precomputed and contains the required metrics.

STRICT RULES:
- Use ONLY the dataset provided below.
- DO NOT ask for more data.
- DO NOT assume missing fields.
- MANDATORY: If numerical computation is required (ranking, adjusted value, comparison), you MUST call a tool. NEVER calculate manually.
- PROVIDE BUSINESS INSIGHTS: Explain WHY the top result is superior (e.g., mention demand, yield, or priority category).
- If the dataset contains only one row but a comparison or ranking is required, inform the user that insufficient data is available for a comparative analysis.
- If the dataset already contains the answer, summarize it directly.

DATASET:
{data_summary}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User Query: {query}"}
    ]

    MAX_STEPS = 3
    rows_count = len(raw_data)
    
    try:
        for step in range(MAX_STEPS):
            if DEBUG:
                print(f"--- Financial Analyst Loop Step {step+1} ---", file=sys.stderr)

            # 1. Call LLM with tools
            response = call_llm(
                messages, 
                tools=FINANCIAL_TOOLS, 
                raw=True, 
                timeout=30
            )
            
            response_message = response['choices'][0]['message']
            
            # 2. MANDATORY: Append assistant message to history.
            # Without this, the LLM loses the tool_calls context in the next turn,
            # causing the tool results to be ignored or causing API errors.
            messages.append(response_message)
            
            tool_calls = response_message.get("tool_calls", [])
            
            # 3. Check if we need to call tools (Early exit)
            if not tool_calls:
                if DEBUG:
                    print("No tool calls requested. Finishing loop.", file=sys.stderr)
                break
                
            # 4. Execute tool calls
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                tool_id = tool_call["id"]
                args_raw = tool_call["function"]["arguments"]
                
                # Safe JSON Parse & Validation
                try:
                    arguments = json.loads(args_raw)
                    if not isinstance(arguments, dict):
                        raise ValueError("Arguments must be an object")
                except Exception as e:
                    print(f"[tool] error parsing args: {e}", file=sys.stderr)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": function_name,
                        "content": json.dumps({"error": "Invalid tool arguments", "details": str(e)})
                    })
                    continue

                # MANDATORY: Log tool execution to verify enforcement
                print(f"[tool] EXECUTING: {function_name} with args: {arguments}", file=sys.stderr)
                
                # Validation & Execution
                if function_name not in TOOL_REGISTRY:
                    result = {"error": "Unknown tool", "tool": function_name}
                else:
                    try:
                        # Execute the pure deterministic function
                        func = TOOL_REGISTRY[function_name]
                        result = func(**arguments)
                    except Exception as e:
                        result = {"error": "Execution failed", "details": str(e)}
                
                if DEBUG:
                    print(f"[tool] result name={function_name} result={result}", file=sys.stderr)
                
                # 5. Append tool result message with mandatory fields
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": function_name,
                    "content": json.dumps(result)
                })
        
        # Final response is the last content from the LLM
        final_content = messages[-1].get("content", "")
        insights = [line.strip() for line in final_content.split('\n') if line.strip()]
        
        meta = {
            'request_id': request_id,
            'rows_used': rows_count,
            'duration_ms': int((time.monotonic() - start_time) * 1000),
            'steps_taken': step + 1
        }

        return {'status': 'success', 'insights': insights, 'meta': meta}

    except Exception as e:
        print(f"Financial Analyst Error: {e}", file=sys.stderr)
        return {
            'status': 'error', 
            'message': 'Financial analysis failed.', 
            'code': 'AGENT_ERROR',
            'meta': {'request_id': request_id, 'details': str(e)}
        }
