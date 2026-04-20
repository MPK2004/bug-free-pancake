import os
import time
import random
from db.connection import get_db_connection
from db.schema import get_schema, format_schema
from db.executor import is_safe_sql, enforce_limit, fix_case, execute_query
from llm.sql_generator import generate_sql
from agents.data_analyst import analyze

def run_pipeline(user_query, request_id=None):
    """
    Orchestrates the NL-to-SQL-to-Analysis pipeline with backoff-enabled recovery.
    Enforces overall deadline and backoff caps for production safety.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        schema_dict = get_schema(cursor)
        schema_str = format_schema(schema_dict)

        sql_query = generate_sql(user_query, schema_str)
        print(f"\nGenerated SQL: {sql_query}")

        sql_query = fix_case(sql_query)
        final_sql = enforce_limit(sql_query)

        if not is_safe_sql(final_sql):
            print("Error: Generated SQL is not safe.")
            return

        print(f"Executing SQL: {final_sql}")

        results = execute_query(cursor, final_sql)

        print("\nResults:")
        for row in results:
            print(row)

        columns = [desc[0] for desc in cursor.description]
        rows_list = [dict(zip(columns, row)) for row in results]
        
        MAX_RETRIES = 3
        MAX_BACKOFF_SECONDS = 10
        DEADLINE_SECONDS = float(os.getenv("LLM_DEADLINE", "20"))
        SAFETY_MARGIN = 0.2
        
        if not hasattr(run_pipeline, "_circuit_states"):
            run_pipeline._circuit_states = {}
        
        CIRCUIT_THRESHOLD = 5
        CIRCUIT_RESET_WINDOW = 60
        
        provider = "openrouter"
        model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        cb_key = f"{provider}:{model}"
        
        if cb_key not in run_pipeline._circuit_states:
            run_pipeline._circuit_states[cb_key] = {"failures": 0, "last_failure": 0, "state": "CLOSED"}
        
        pipeline_start = time.monotonic()
        result = None
        attempt_summary = []
        
        for attempt in range(1, MAX_RETRIES + 1):
            now = time.monotonic()
            cb = run_pipeline._circuit_states[cb_key]
            
            if cb["state"] == "OPEN" and (now - cb["last_failure"] > CIRCUIT_RESET_WINDOW):
                cb["state"] = "HALF_OPEN"
                print(f"[RECOVER] [{request_id}] Circuit {cb_key} transitioned to HALF_OPEN. Probing...")

            if cb["state"] == "OPEN":
                result = {
                    "status": "error", "type": "internal_transient", "code": "CIRCUIT_OPEN", 
                    "message": f"Circuit {cb_key} is OPEN. Upstream unstable.", 
                    "meta": {"attempts": attempt-1, "total_duration_ms": int((now - pipeline_start) * 1000)}
                }
                break
            
            remaining_s = DEADLINE_SECONDS - (now - pipeline_start)
            if remaining_s <= SAFETY_MARGIN:
                result = {
                    "status": "error", "type": "timeout", "code": "DEADLINE_EXCEEDED",
                    "message": f"Exceeded overall deadline ({DEADLINE_SECONDS}s).",
                    "meta": {"request_id": request_id, "attempts": attempt - 1, "total_duration_ms": int((now - pipeline_start) * 1000)}
                }
                break

            analysis_context = {
                "user_query": user_query, "data": rows_list, "request_id": request_id,
                "attempt": attempt, "deadline_s": DEADLINE_SECONDS, "remaining_s": remaining_s,
                "model": model, "region": os.getenv("LLM_REGION", "auto")
            }
            
            attempt_start = time.monotonic()
            result = analyze(analysis_context)
            attempt_duration = int((time.monotonic() - attempt_start) * 1000)
            
            err_code = result.get("code", "UNKNOWN")
            
            attempt_summary.append({
                "attempt": attempt, 
                "code": err_code if result["status"] == "error" else "SUCCESS",
                "status_code": result.get("status_code", 200),
                "duration_ms": attempt_duration
            })
            
            if result["status"] == "success":
                if cb["state"] == "HALF_OPEN":
                    cb["state"] = "CLOSED"
                    cb["failures"] = 0
                    print(f"[RECOVER] [{request_id}] Probe successful. Circuit {cb_key} CLOSED.")
                cb["failures"] = 0 

                total_duration = int((time.monotonic() - pipeline_start) * 1000)
                print(f"[METRIC] [analysis.success.count] [request_id={request_id}] [attempts={attempt}] [total_duration_ms={total_duration}]")
                break
            
            if result.get("type") in ["timeout", "internal_transient"]:
                 cb["failures"] += 1
                 cb["last_failure"] = time.monotonic()
                 if cb["state"] == "HALF_OPEN" or cb["failures"] >= CIRCUIT_THRESHOLD:
                     cb["state"] = "OPEN"
                     print(f"[BREAKER] [{request_id}] Circuit {cb_key} transitioned to OPEN.")

            if os.getenv("DEBUG", "false").lower() == "true" and random.random() < 0.1:
                print(f"[DEBUG] [sample] attempt {attempt} failed with {err_code}", file=sys.stderr)

            if result.get("type") in ["timeout", "internal_transient"] and attempt < MAX_RETRIES:
                base = 3 if err_code == "RATE_LIMITED_429" else 2
                raw_delay = (base ** (attempt - 1)) + random.uniform(0, 1)
                delay = min(raw_delay, MAX_BACKOFF_SECONDS)
                
                remaining_after_call = DEADLINE_SECONDS - (time.monotonic() - pipeline_start)
                sleep_for = min(delay, max(0, remaining_after_call - SAFETY_MARGIN))
                
                if sleep_for <= 0:
                    print(f"[METRIC] [analysis.retry.cutoff] [request_id={request_id}]")
                    break
                
                print(f"[RETRY] [analysis.retry.count] [request_id={request_id}] [code={err_code}] [attempt={attempt}] Retrying in {sleep_for:.2f}s...")
                time.sleep(sleep_for)
            else:
                break
        
        if result and "meta" in result:
            result["meta"]["attempt_summary"] = attempt_summary
            result["meta"]["total_duration_ms"] = int((time.monotonic() - pipeline_start) * 1000)

        print("\nANALYSIS:")
        if result["status"] == "success":
            for i, insight in enumerate(result["insights"], 1):
                print(f"{i}. {insight}")
            return result["insights"]
        else:
            final_code = result.get("code", "ERROR")
            final_req_id = result.get("meta", {}).get("request_id", "UNKNOWN")
            final_duration = int((time.monotonic() - pipeline_start) * 1000)
            print(f"[ERROR] [{final_req_id}] [code={final_code}] [attempt={attempt}] [provider={provider}] [total_duration_ms={final_duration}] {result.get('message')}")
            print(f"[METRIC] [analysis.error.{final_code}.count] [request_id={final_req_id}]")
            return result.get("message")

    finally:
        conn.close()
