import time
import json
import os
from collections import Counter
from threading import Lock
from agents import data_analyst, financial_analyst, general_responder
from llm.client import call_llm

# Thread-safe Intent Distribution Tracking
INTENT_COUNTS = Counter({"DATA_ANALYSIS": 0, "FINANCIAL_ANALYSIS": 0, "GENERAL": 0})
LOCK = Lock()

def plan_tasks(query: str, history: list = None) -> list:
    """
    Decomposes the user's query into a sequence of atomic tasks.
    Returns a list of dicts: [{"intent": "...", "sub_query": "..."}]
    
    Strictly uses the FAST_LLM_MODEL for low-latency planning.
    """
    history_context = ""
    if history:
        history_context = "RECENT CONVERSATION:\n"
        for msg in history:
            role = msg['role'].upper()
            content = msg['content'][:200]
            history_context += f"{role}: {content}\n"
        history_context += "\n"

    prompt = f"""
{history_context}You are the Task Planner for a Mall Leasing AI. 
Decompose the user's query into a sequence of atomic tasks.

INTENT TYPES:
1. DATA_ANALYSIS: Specific data lookups, counting, or filtering.
2. FINANCIAL_ANALYSIS: Strategic decisions, rankings, comparisons, or adjusted value calculations.
3. GENERAL: Greetings, conceptual explanations, or drafting documents (emails, reports) based on data.

RULES:
- If a query asks to calculate something AND then do something else (like email it), split it into TWO tasks.
- The first task should always be the data/financial analysis if the second task depends on its results.
- Return ONLY a JSON array of tasks.

EXAMPLES:
Query: "How many transactions were there and why does yield matter?"
Response: [
    {{"intent": "DATA_ANALYSIS", "sub_query": "How many transactions were there?"}},
    {{"intent": "GENERAL", "sub_query": "Explain why yield matters in leasing."}}
]

Query: "Calculate strategic value for Zara and draft an email to them."
Response: [
    {{"intent": "FINANCIAL_ANALYSIS", "sub_query": "Calculate strategic value for Zara proposal."}},
    {{"intent": "GENERAL", "sub_query": "Draft a formal email to Zara summarizing their strategic value results."}}
]

Query: {query}
"""
    fast_model = os.getenv("FAST_LLM_MODEL")
    start_time = time.monotonic()
    
    try:
        response = call_llm([{"role": "user", "content": prompt}], model=fast_model)
        # Extract JSON array
        import re
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            tasks = json.loads(match.group())
        else:
            # Fallback to single classification if planning fails
            intent = classify_intent(query, history)
            tasks = [{"intent": intent, "sub_query": query}]
            
        duration_ms = int((time.monotonic() - start_time) * 1000)
        print(json.dumps({
            "event": "task_planning",
            "task_count": len(tasks),
            "model": fast_model,
            "duration_ms": duration_ms,
            "query": query[:50]
        }))
        
        # Track intents for metrics
        with LOCK:
            for t in tasks:
                INTENT_COUNTS[t['intent']] += 1
                
        return tasks
    except Exception as e:
        print(f"[router] Planning failed: {e}. Falling back to single classification.")
        intent = classify_intent(query, history)
        return [{"intent": intent, "sub_query": query}]

def classify_intent(query: str, history: list = None) -> str:
    """
    Fallback/Single-step classification logic.
    """

def route(query, results, intent=None):
    """
    Decides which agent should handle the query based on classified intent.
    Returns the agent module.
    """
    # If intent is not passed, classify it (though pipeline should handle this)
    if not intent:
        intent = classify_intent(query)

    if intent == "FINANCIAL_ANALYSIS":
        return financial_analyst
    
    if intent == "GENERAL":
        return general_responder
        
    return data_analyst
