import os
import re
import sys
import uuid
import time
from llm.client import call_llm, LLMAuthError, LLMRateLimitError, LLMOverloadError, LLMError

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
MAX_ROWS = 50
MAX_FIELD_LENGTH = 200
MAX_RESPONSE_CHARS = 5000

def redact(s: str) -> str:
    """Masks API keys, Auth headers, cookies, and strips PII/Credentialed URLs."""
    if not isinstance(s, str):
        return s
    # Mask API keys (sk-...)
    s = re.sub(r'(sk-[A-Za-z0-9]{20,})', '****', s)
    # Mask Bearer tokens / Authorization headers in bodies or headers
    s = re.sub(r'(Authorization:?\s*Bearer\s+)[A-Za-z0-9\-\._~+/]+=*', r'\1****', s, flags=re.IGNORECASE)
    # Mask Cookie values
    s = re.sub(r'(Cookie:?\s*)[^(\s|;)]+', r'\1****', s, flags=re.IGNORECASE)
    # Strip URL query params
    s = re.sub(r'(https?://\S+?)\?.*?(?=\s|$)', r'\1', s)
    return s

def _normalize(s: str) -> str:
    """Surgical normalization: Collapses whitespace, lowercases, preserves semantic / % - +."""
    # Collapse multiple spaces and trim
    s = re.sub(r'\s+', ' ', s).strip().lower()
    # Keep alphanumeric characters and semantic operators/marks
    return re.sub(r'[^a-z0-9\s/%+\-]', '', s)

def _safe_stringify(val):
    """Safely stringify and trim values. Returns (string, was_truncated)."""
    s = str(val)
    if len(s) > MAX_FIELD_LENGTH:
        return s[:MAX_FIELD_LENGTH] + "...", True
    return s, False

def _clean_line(line: str) -> str:
    """Removes common list prefixes (-, *, 1., 2)) from the start of a line."""
    return re.sub(r'^\s*(?:[-*]|\d+[\.\)])\s*', '', line).strip()

def _is_weak(s: str) -> bool:
    """Filter out extremely short noise (e.g., 'Yes.', 'Analysis:')"""
    return len(s.split()) < 3

def analyze(context: dict):
    """
    Analyzes SQL results with extreme production grade safety and telemetry.
    """
    start_cpu = time.monotonic()
    
    if not isinstance(context, dict):
        return {
            "status": "error", "type": "validation", "code": "VALIDATION_ERROR",
            "message": "Invalid input: context must be a dictionary.",
            "meta": {"request_id": str(uuid.uuid4()), "attempts": 1, "insight_count": 0}
        }
    
    request_id = context.get("request_id") or str(uuid.uuid4())
    attempt = context.get("attempt", 1)
    deadline_sec = context.get("deadline_s", 20.0)
    remaining_sec = context.get("remaining_s", deadline_sec)
    
    meta = {
        "request_id": request_id, 
        "attempt_id": f"{request_id}:{attempt}",
        "attempts": attempt, 
        "rows_used": 0, 
        "row_truncated": False,
        "field_truncated": False, 
        "insight_count": 0, 
        "source": "llm",
        "provider": "openrouter",
        "model": context.get("model", "gpt-3.5-turbo"),
        "region": context.get("region", "auto"),
        "response_truncated": False,
        "deadline_ms": int(deadline_sec * 1000),
        "remaining_ms": max(0, int(remaining_sec * 1000))
    }
    
    user_query = context.get("user_query")
    data = context.get("data")

    if not isinstance(user_query, str) or not user_query.strip():
        return {
            "status": "error", 
            "type": "validation", "code": "INVALID_QUERY",
            "message": "Invalid input: user_query must be a non-empty string.",
            "meta": meta
        }
    
    if not isinstance(data, list):
        return {
            "status": "error", 
            "type": "validation", "code": "INVALID_DATA_FORMAT",
            "message": "Invalid input: data must be a list.",
            "meta": meta
        }

    if not data:
        return {
            "status": "success", 
            "insights": ["No data available for the given query. Unable to derive insights."],
            "meta": meta
        }

    meta["rows_used"] = len(data)
    if len(data) > MAX_ROWS:
        meta["row_truncated"] = True
        data = data[:MAX_ROWS]

    processed_data = []
    for row in data:
        row_processed = {}
        if isinstance(row, dict):
            for k, v in row.items():
                val_str, truncated = _safe_stringify(v)
                row_processed[k] = val_str
                if truncated:
                    meta["field_truncated"] = True
            processed_data.append(row_processed)
        else:
            val_str, truncated = _safe_stringify(row)
            processed_data.append(val_str)
            if truncated:
                meta["field_truncated"] = True

    analysis_prompt = f"User Question: {user_query}\nData: {processed_data}\n\nSTRICT RULES: 3-5 concise bullet points. Use '-' prefix."

    if DEBUG:
        print(f"--- LLM Input [ID: {meta['request_id']}] ---", file=sys.stderr)
        print(redact(analysis_prompt), file=sys.stderr)

    llm_start = time.monotonic()
    try:
        response = call_llm([{"role": "user", "content": analysis_prompt}], timeout=max(1, remaining_sec))
        
        if len(response) > MAX_RESPONSE_CHARS:
            response = response[:MAX_RESPONSE_CHARS] + "...[truncated]"
            meta["response_truncated"] = True
        
        meta["llm_duration_ms"] = int((time.monotonic() - llm_start) * 1000)
        meta["total_duration_ms"] = int((time.monotonic() - start_cpu) * 1000)
        
        if DEBUG:
            print(f"--- LLM Output [{meta['attempt_id']}] ---\n{redact(response)}", file=sys.stderr)

        MAX_INSIGHTS = 5
        MAX_PARSE_PASSES = 2
        MAX_CANDIDATES = 50
        
        raw_lines = response.split("\n")
        
        if len(raw_lines) > MAX_CANDIDATES:
            raw_lines = raw_lines[:MAX_CANDIDATES]
            
        insights = []
        seen_normalized = set()
        
        for _ in range(MAX_PARSE_PASSES):
            if len(insights) >= MAX_INSIGHTS: break
            
            for line in raw_lines:
                if len(insights) >= MAX_INSIGHTS: break
                
                segments = [line]
                if re.search(r'\d+[\.\)]', line):
                     segments = re.split(r'\s(?=\d+[\.\)])', line)
                
                for seg in segments:
                    cleaned = _clean_line(seg)
                    if cleaned and not _is_weak(cleaned):
                        norm_key = _normalize(cleaned)
                        if norm_key not in seen_normalized:
                            seen_normalized.add(norm_key)
                            insights.append(cleaned)
                            if len(insights) >= MAX_INSIGHTS: break
            break 
        
        final_insights = insights[:MAX_INSIGHTS]
        meta["insight_count"] = len(final_insights)

        return {"status": "success", "insights": final_insights, "meta": meta}

    except Exception as e:
        meta["llm_duration_ms"] = int((time.perf_counter() - llm_start) * 1000)
        meta["total_duration_ms"] = int((time.perf_counter() - start_cpu) * 1000)
        error_msg = str(e)
        
        status_code = getattr(e, 'status_code', 500)
        err_type = "internal_fatal"; err_code = "INTERNAL_PROCESSING_ERROR"
        
        if isinstance(e, LLMAuthError):
            err_type = "auth"; err_code = "AUTH_INVALID_KEY"
        elif isinstance(e, LLMRateLimitError):
            err_type = "internal_transient"; err_code = "RATE_LIMITED_429"
        elif isinstance(e, LLMOverloadError):
            err_type = "internal_transient"; err_code = "SERVICE_UNAVAILABLE_503"
        elif "timeout" in error_msg.lower() or status_code == 408:
            err_type = "timeout"; err_code = "LLM_TIMEOUT"
        elif status_code >= 500:
            err_type = "internal_transient"; err_code = f"SERVER_ERROR_{status_code}"

        if DEBUG:
            print(f"LLM Error [{meta['attempt_id']}]: [status={status_code}] {redact(error_msg)}", file=sys.stderr)
            
        return {
            "status": "error", "type": err_type, "code": err_code, "status_code": status_code,
            "message": redact(error_msg) if err_type != 'internal_fatal' else 'Analysis failed.',
            "meta": meta
        }
