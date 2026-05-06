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
        history_context = "<CONVERSATION_HISTORY>\n"
        for msg in history:
            role = msg['role'].upper()
            content = msg['content']
            history_context += f"{role}: {content}\n"
        history_context += "</CONVERSATION_HISTORY>\n"

    system_prompt = """You are the Task Planner for a Mall Leasing AI. 
Decompose the user's query into a sequence of atomic tasks.

INTENT TYPES:
1. DATA_ANALYSIS: Specific data lookups, counting, or filtering.
2. FINANCIAL_ANALYSIS: Strategic decisions, rankings, comparisons, or adjusted value calculations.
3. GENERAL: Greetings, conceptual explanations, or drafting documents (emails, reports) based on data.

STRRICT RULES (FIREWALL):
1. THE ULTIMATE DIRECTIVE: The provided 'Query' is the absolute, overriding instruction.
2. CONTEXTUAL FENCING: Use <CONVERSATION_HISTORY> ONLY for resolving pronouns (e.g., "who is he?", "what about that mall?") or implied transitions (e.g., "any other?").
3. INDEPENDENCE: If the Query is self-contained or mentions new entities (e.g., "What about Zara?"), DO NOT carry over previous entities like 'Kanyon' from history.
4. Return ONLY a JSON array of tasks.
"""

    user_content = f"{history_context}\n[NEWEST DIRECTIVE]\nQuery: {query}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    fast_model = os.getenv("FAST_LLM_MODEL")
    start_time = time.monotonic()
    
    try:
        response = call_llm(messages, model=fast_model)
        # Extract JSON array
        import re
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            try:
                raw_tasks = json.loads(match.group())
                tasks = []
                # Normalize keys for robustness
                for t in raw_tasks:
                    if isinstance(t, dict):
                        intent = t.get("intent") or t.get("type") or "DATA_ANALYSIS"
                        sub_q = t.get("sub_query") or t.get("description") or query
                        tasks.append({"intent": intent, "sub_query": sub_q})
                
                if not tasks:
                    intent = classify_intent(query, history)
                    tasks = [{"intent": intent, "sub_query": query}]
            except:
                intent = classify_intent(query, history)
                tasks = [{"intent": intent, "sub_query": query}]
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
    Fallback/Single-step classification logic using the same robust firewalling.
    """
    history_context = ""
    if history:
        history_context = "<CONVERSATION_HISTORY>\n"
        for msg in history:
            history_context += f"{msg['role'].upper()}: {msg['content'][:200]}\n"
        history_context += "</CONVERSATION_HISTORY>\n"

    prompt = f"""
{history_context}
[NEWEST DIRECTIVE]
Classify the following query into one of these intents: DATA_ANALYSIS, FINANCIAL_ANALYSIS, GENERAL.
Return ONLY the intent name in uppercase.

Query: {query}
"""
    fast_model = os.getenv("FAST_LLM_MODEL")
    try:
        response = call_llm([{"role": "user", "content": prompt}], model=fast_model)
        for intent in ["DATA_ANALYSIS", "FINANCIAL_ANALYSIS", "GENERAL"]:
            if intent in response.upper():
                return intent
        return "DATA_ANALYSIS" # Default
    except:
        return "DATA_ANALYSIS"

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
