import os
import time
import random
import sys
from db.connection import get_db_connection
from db.schema import get_schema, format_schema
from db.executor import is_safe_sql, enforce_limit, fix_case, execute_query
from llm.sql_generator import generate_sql
from orchestrator import router
from orchestrator.memory import ConversationHistory

def get_analysis_mode(intent):
    """
    Maps classified intent to SQL generation mode.
    """
    if intent == "FINANCIAL_ANALYSIS":
        return "strategic"
    return "analytical"

def run_pipeline(user_query, history=None, request_id=None):
    """
    Orchestrates the NL-to-SQL-to-Analysis pipeline with a Multi-Model Cascade.
    """
    pipeline_start = time.monotonic()
    
    # Load model configuration
    FAST_MODEL = os.getenv("FAST_LLM_MODEL")
    SMART_MODEL = os.getenv("SMART_LLM_MODEL")
    
    # 1. Intent Classification (The "Routing Brain")
    # Uses truncated history for context-aware routing (pronoun resolution).
    try:
        clean_history = history.get_clean_history() if history else []
        intent = router.classify_intent(user_query, history=clean_history)
    except Exception as e:
        print(f"[pipeline.error] Router failed: {e}. Falling back to GENERAL.")
        intent = "GENERAL"
    
    print(f"Detected intent: {intent}")

    # 2. Multi-Model Cascade Decision
    # Cognitive Alignment: The model for SQL and Analysis mirrors the task complexity.
    if intent == "FINANCIAL_ANALYSIS":
        active_model = SMART_MODEL
    else:
        active_model = FAST_MODEL
        
    print(f"Active model for cascade: {active_model}")

    rows_list = []
    
    # 3. Data Acquisition (Skip if GENERAL)
    if intent != "GENERAL":
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            schema_dict = get_schema(cursor)
            analysis_mode = get_analysis_mode(intent)
            
            # Pass history for pronoun resolution in SQL generation
            truncated_history = history.get_truncated() if history else []
            sql_query = generate_sql(user_query, schema_dict, history=truncated_history, mode=analysis_mode, model=active_model)
            
            MAX_SQL_ATTEMPTS = 2
            results = None
            sql_to_execute = sql_query

            for sql_attempt in range(MAX_SQL_ATTEMPTS):
                try:
                    # Clean and Enforce
                    final_sql = fix_case(sql_to_execute)
                    final_sql = enforce_limit(final_sql)

                    if not is_safe_sql(final_sql):
                        raise Exception("Insecure SQL generated.")

                    print(f"Executing SQL (Attempt {sql_attempt + 1}): {final_sql}")
                    results = execute_query(cursor, final_sql)
                    break # Success!
                except Exception as e:
                    last_error = str(e)
                    print(f"SQL Execution Failed: {last_error}")
                    
                    if sql_attempt < MAX_SQL_ATTEMPTS - 1:
                        print("Attempting agentic self-correction...")
                        feedback = {
                            "error": last_error,
                            "previous_sql": sql_to_execute
                        }
                        sql_to_execute = generate_sql(
                            user_query, 
                            schema_dict, 
                            history=truncated_history, 
                            mode=analysis_mode, 
                            model=active_model,
                            feedback=feedback
                        )
                    else:
                        raise e # Out of attempts

            if results is None:
                raise Exception("SQL Acquisition failed after multiple attempts.")
            
            columns = [desc[0] for desc in cursor.description]
            rows_list = [dict(zip(columns, row)) for row in results]
        finally:
            conn.close()
    else:
        print("Skipping SQL generation for GENERAL intent.")

    # 4. Agent Selection & Analysis Loop
    agent = router.route(user_query, rows_list, intent=intent)
    print(f"Selected agent: {agent.NAME}")

    MAX_RETRIES = 3
    MAX_BACKOFF_SECONDS = 10
    DEADLINE_SECONDS = float(os.getenv("LLM_DEADLINE", "20"))
    SAFETY_MARGIN = 0.2
    
    if not hasattr(run_pipeline, "_circuit_states"):
        run_pipeline._circuit_states = {}
    
    CIRCUIT_THRESHOLD = 5
    CIRCUIT_RESET_WINDOW = 60
    
    # Circuit breaker key now includes the specific model in the cascade
    provider = "openrouter"
    cb_key = f"{provider}:{active_model}"
    
    if cb_key not in run_pipeline._circuit_states:
        run_pipeline._circuit_states[cb_key] = {"failures": 0, "last_failure": 0, "state": "CLOSED"}
    
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

        # Inject context and history for the agent
        analysis_context = {
            "query": user_query, 
            "data": rows_list, 
            "history": history.get_full() if history else [],
            "request_id": request_id,
            "attempt": attempt, 
            "deadline_s": DEADLINE_SECONDS, 
            "remaining_s": remaining_s,
            "model": active_model, 
            "region": os.getenv("LLM_REGION", "auto")
        }
        
        attempt_start = time.monotonic()
        result = agent.analyze(analysis_context)
        
        if result is None:
            print(f"[pipeline.error] Agent {agent.NAME} returned None result.", file=sys.stderr)
            result = {"status": "error", "message": "Agent returned null result.", "code": "AGENT_NULL"}
            
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
            cb["failures"] = 0 
            break
        
        if result.get("type") in ["timeout", "internal_transient"]:
             cb["failures"] += 1
             cb["last_failure"] = time.monotonic()
             if cb["state"] == "HALF_OPEN" or cb["failures"] >= CIRCUIT_THRESHOLD:
                 cb["state"] = "OPEN"

        if result.get("type") in ["timeout", "internal_transient"] and attempt < MAX_RETRIES:
            base = 3 if err_code == "RATE_LIMITED_429" else 2
            raw_delay = (base ** (attempt - 1)) + random.uniform(0, 1)
            delay = min(raw_delay, MAX_BACKOFF_SECONDS)
            remaining_after_call = DEADLINE_SECONDS - (time.monotonic() - pipeline_start)
            sleep_for = min(delay, max(0, remaining_after_call - SAFETY_MARGIN))
            if sleep_for <= 0: break
            time.sleep(sleep_for)
        else:
            break
    
    if result and "meta" in result:
        result["meta"]["attempt_summary"] = attempt_summary
        result["meta"]["total_duration_ms"] = int((time.monotonic() - pipeline_start) * 1000)

    print("\nANALYSIS:")
    final_output = ""
    if result["status"] == "success":
        final_output = "\n".join(result["insights"])
        print(final_output)
        
        # 5. Persist to History & Compact
        if history:
            # We append the final response to the history
            history.append("assistant", final_output)
            # Check for compaction
            history.compact(model=FAST_MODEL)
            
        return result["insights"]
    else:
        final_output = result.get("message", "Analysis failed.")
        if history:
            history.append("assistant", f"ERROR: {final_output}")
        return final_output
