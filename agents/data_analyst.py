import os
import re
import sys
from llm.client import call_llm

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
MAX_ROWS = 50
MAX_FIELD_LENGTH = 200

def _safe_stringify(val):
    """Safely stringify and trim values."""
    s = str(val)
    if len(s) > MAX_FIELD_LENGTH:
        return s[:MAX_FIELD_LENGTH] + "..."
    return s

def _clean_line(line: str) -> str:
    """Removes common list prefixes (-, *, 1., 2)) from the start of a line."""
    return re.sub(r'^\s*(?:[-*]|\d+[\.\)])\s*', '', line).strip()

def _is_weak(s: str) -> bool:
    """Filter out fluff or extremely short insights."""
    return len(s.split()) < 4

def analyze(context: dict):
    """
    Analyzes SQL results and provides a natural language summary.
    Expects context: {"user_query": str, "data": list[dict]}
    """
    # 1. Manual Validation
    if not isinstance(context, dict):
        return {"status": "error", "message": "Invalid input: context must be a dictionary."}
    
    user_query = context.get("user_query")
    data = context.get("data")

    if not isinstance(user_query, str) or not user_query.strip():
        return {"status": "error", "message": "Invalid input: user_query must be a non-empty string."}
    
    if not isinstance(data, list):
        return {"status": "error", "message": "Invalid input: data must be a list."}

    # 2. Empty Data Handling
    if not data:
        return {
            "status": "success", 
            "insights": ["No data available for the given query. Unable to derive insights."],
            "meta": {"rows_used": 0}
        }

    # 3. Data Processing (Trimming & Stringification)
    processed_data = []
    for row in data[:MAX_ROWS]:
        if isinstance(row, dict):
            processed_data.append({k: _safe_stringify(v) for k, v in row.items()})
        else:
            processed_data.append(_safe_stringify(row))

    # 4. Prompt Construction
    analysis_prompt = f"""
You are an expert data analyst. Directly answer the user's query using the provided SQL results.

User Question:
{user_query}

Data (Top {MAX_ROWS} rows):
{processed_data}

STRICT RULES:
- Start with insights that directly address the user's query.
- Each bullet should be 1–2 sentences maximum.
- Use "-" for each bullet point.
- Do not infer or fabricate missing data.
- Do not speculate beyond the provided data.
- Base insights only on visible data, not assumptions about unseen data.
- Only a subset of data may be provided (indicated by truncation or row limits); treat "... " as partial data.
- If the data does not support meaningful insights, explicitly state that.

OUTPUT:
- 3 to 5 concise bullet points
"""

    if DEBUG:
        print(f"--- Agent Input ---\n{analysis_prompt}", file=sys.stderr)

    # 5. LLM Call
    try:
        response = call_llm([{"role": "user", "content": analysis_prompt}])
        
        if DEBUG:
            print(f"--- Agent Output ---\n{response}", file=sys.stderr)

        # 6. Robust Parsing
        lines = response.split("\n")
        insights = [_clean_line(l) for l in lines if _clean_line(l)]
        
        # Filter weak signals
        insights = [i for i in insights if not _is_weak(i)]
        
        # Fallback if parsing fails
        if not insights:
            insights = [response.strip()]
            
        # Cap results
        insights = insights[:5]

        return {
            "status": "success",
            "insights": insights,
            "meta": {"rows_used": len(processed_data)}
        }

    except Exception as e:
        if DEBUG:
            print(f"LLM Error: {e}", file=sys.stderr)
        return {
            "status": "error", 
            "message": "Analysis failed due to timeout or processing error. Please retry."
        }
