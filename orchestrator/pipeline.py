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

def extract_entities(rows):
    """
    Extracts key identifiers (mall names, brand names) from database rows
    to anchor the data context for future turns.
    """
    if not rows:
        return []
    
    identity_keys = {"tenant", "shopping_mall", "category", "brand", "entity_identifier", "dominant_category"}
    entities = set()
    for row in rows[:10]: # Check top results for context
        for k, v in row.items():
            if k.lower() in identity_keys and v:
                entities.add(str(v))
    return list(entities)

def get_analysis_mode(intent):
    """
    Maps classified intent to SQL generation mode.
    """
    if intent == "FINANCIAL_ANALYSIS":
        return "strategic"
    return "analytical"

def execute_step(task, history, active_model, FAST_MODEL, request_id=None):
    """
    Executes a single atomic task (one step in the execution graph).
    Returns (result_string, rows_list).
    """
    intent = task['intent']
    sub_query = task['sub_query']
    rows_list = []
    
    # 1. Data Acquisition (Skip if GENERAL)
    if intent != "GENERAL":
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            schema_dict = get_schema(cursor)
            analysis_mode = get_analysis_mode(intent)
            
            # Use Clean History (Synthetic Data Context) for SQL generation to avoid noise
            truncated_history = history.get_clean_history()
            
            sql_query = generate_sql(sub_query, schema_dict, history=truncated_history, mode=analysis_mode, model=active_model)
            
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

                    print(f"[{intent}] Executing SQL (Attempt {sql_attempt + 1}): {final_sql}")
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
                            sub_query, 
                            schema_dict, 
                            history=truncated_history, 
                            mode=analysis_mode, 
                            model=active_model,
                            feedback=feedback
                        )
                    else:
                        raise e # Out of attempts

            if results is None:
                raise Exception("SQL Acquisition failed.")
            
            columns = [desc[0] for desc in cursor.description]
            rows_list = [dict(zip(columns, row)) for row in results]
        finally:
            conn.close()

    # 2. Agent Selection & Analysis Loop
    agent = router.route(sub_query, rows_list, intent=intent)
    
    MAX_RETRIES = 3
    DEADLINE_SECONDS = float(os.getenv("LLM_DEADLINE", "30"))
    SAFETY_MARGIN = 0.2
    
    step_start = time.monotonic()
    
    for attempt in range(1, MAX_RETRIES + 1):
        remaining_s = DEADLINE_SECONDS - (time.monotonic() - step_start)
        if remaining_s <= SAFETY_MARGIN:
            return "Analysis timed out.", rows_list

        analysis_context = {
            "query": sub_query, 
            "data": rows_list, 
            "history": history.get_full(), # Analyst gets the rich history (snapshot + messages)
            "request_id": request_id,
            "attempt": attempt, 
            "deadline_s": DEADLINE_SECONDS, 
            "remaining_s": remaining_s,
            "model": active_model
        }
        
        result = agent.analyze(analysis_context)
        
        if result["status"] == "success":
            return "\n".join(result["insights"]), rows_list
        
        # Exponential backoff on transient errors
        if result.get("type") in ["timeout", "internal_transient"] and attempt < MAX_RETRIES:
            time.sleep(min(2 ** attempt, 5))
        else:
            break
            
    return result.get("message", "Analysis failed."), rows_list

def run_pipeline(user_query, request_id=None, history=None):
    """
    Generator that orchestrates the execution graph and yields status events.
    """
    if history is None:
        history = ConversationHistory()
        
    FAST_MODEL = os.getenv("FAST_LLM_MODEL")
    SMART_MODEL = os.getenv("SMART_LLM_MODEL")

    # 1. Planning Step
    yield {"event": "planning", "status": "Decomposing query into tasks..."}
    try:
        # Use Hybrid Context (Entities + Conclusion) for routing
        router_history = history.get_router_history(limit=3)
        tasks = router.plan_tasks(user_query, history=router_history)
    except Exception as e:
        print(f"[pipeline] Planning error: {e}")
        tasks = [{"intent": "GENERAL", "sub_query": user_query}]
    
    yield {"event": "plan_ready", "tasks": tasks}

    # Pre-append user query to anchor context for all steps
    history.append("user", user_query)

    full_results = []
    
    for i, task in enumerate(tasks):
        intent = task['intent']
        
        yield {"event": "step_start", "index": i + 1, "task": task}

        # Select model based on intent complexity
        active_model = SMART_MODEL if intent == "FINANCIAL_ANALYSIS" else FAST_MODEL
        
        try:
            step_insights, rows_list = execute_step(task, history, active_model, FAST_MODEL, request_id=request_id)
            
            # Anchor entities and intent to history for next turn/step resolution
            entities = extract_entities(rows_list)
            history.append("assistant", step_insights, entities=entities, intent=intent)
            
            full_results.append(step_insights)
            yield {"event": "step_complete", "index": i + 1, "insights": step_insights}
        except Exception as e:
            error_msg = f"Step {i+1} failed: {e}"
            print(f"[pipeline] {error_msg}")
            history.append("assistant", f"ERROR: {error_msg}")
            full_results.append(error_msg)
            yield {"event": "step_complete", "index": i + 1, "insights": error_msg}

    # Final maintenance (Compaction)
    history.compact(model=FAST_MODEL)
    
    yield {"event": "pipeline_complete", "results": full_results}
