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
            
            # Pass sub_query for precise SQL generation
            sql_query = generate_sql(sub_query, schema_dict, mode=analysis_mode, model=active_model, history=history.get_clean_history())
            print(f"\n[{intent}] Generated SQL: {sql_query}")

            sql_query = fix_case(sql_query)
            final_sql = enforce_limit(sql_query)

            if not is_safe_sql(final_sql):
                return "Error: Insecure query generated.", []

            results = execute_query(cursor, final_sql)
            columns = [desc[0] for desc in cursor.description]
            rows_list = [dict(zip(columns, row)) for row in results]
        finally:
            conn.close()

    # 2. Agent Selection & Analysis Loop
    agent = router.route(sub_query, rows_list, intent=intent)
    
    MAX_RETRIES = 3
    DEADLINE_SECONDS = float(os.getenv("LLM_DEADLINE", "30"))
    SAFETY_MARGIN = 0.2
    
    # Simple Circuit Breaker logic (stateless for the step, persistent for the process)
    if not hasattr(execute_step, "_circuit_states"):
        execute_step._circuit_states = {}
    
    cb_key = f"openrouter:{active_model}"
    if cb_key not in execute_step._circuit_states:
        execute_step._circuit_states[cb_key] = {"failures": 0, "last_failure": 0, "state": "CLOSED"}

    step_start = time.monotonic()
    result = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        remaining_s = DEADLINE_SECONDS - (time.monotonic() - step_start)
        if remaining_s <= SAFETY_MARGIN:
            return "Analysis timed out.", rows_list

        analysis_context = {
            "query": sub_query, 
            "data": rows_list, 
            "history": history.get_full(),
            "request_id": request_id,
            "attempt": attempt, 
            "deadline_s": DEADLINE_SECONDS, 
            "remaining_s": remaining_s,
            "model": active_model, 
            "region": os.getenv("LLM_REGION", "auto")
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
        
    pipeline_start = time.monotonic()
    FAST_MODEL = os.getenv("FAST_LLM_MODEL")
    SMART_MODEL = os.getenv("SMART_LLM_MODEL")

    # 1. Planning Step
    yield {"event": "planning", "status": "Decomposing query into tasks..."}
    try:
        tasks = router.plan_tasks(user_query, history=history.get_router_history(limit=3))
    except Exception as e:
        tasks = [{"intent": "GENERAL", "sub_query": user_query}]
    
    yield {"event": "plan_ready", "tasks": tasks}

    # Pre-append user query to anchor context for all steps
    history.append("user", user_query)

    full_results = []
    
    for i, task in enumerate(tasks):
        intent = task['intent']
        sub_query = task['sub_query']
        
        yield {"event": "step_start", "index": i + 1, "task": task}

        # Select model based on intent complexity
        active_model = SMART_MODEL if intent == "FINANCIAL_ANALYSIS" else FAST_MODEL
        
        step_insights, rows_list = execute_step(task, history, active_model, FAST_MODEL, request_id=request_id)
        
        # Anchor entities to history for next turn/step resolution
        entities = extract_entities(rows_list)
        history.append("assistant", step_insights, entities=entities, intent=intent)
        
        full_results.append(step_insights)
        
        yield {"event": "step_complete", "index": i + 1, "insights": step_insights}

    # Final maintenance
    history.compact(model=FAST_MODEL)
    
    yield {"event": "pipeline_complete", "results": full_results}

