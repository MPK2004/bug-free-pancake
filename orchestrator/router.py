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

def classify_intent(query: str) -> str:
    """
    Classifies the user's query into ONE of the following categories:
    1. DATA_ANALYSIS -> database queries (counts, filters, aggregations)
    2. FINANCIAL_ANALYSIS -> calculations, comparisons, or financial metrics
    3. GENERAL -> general knowledge, explanations, or greeting

    Strictly uses the FAST_LLM_MODEL to minimize latency for routing.
    """
    prompt = f"""
Classify the user's query into ONE of the following categories:

1. DATA_ANALYSIS → Use for specific data lookups, counting, or filtering (e.g., "How many transactions?").
2. FINANCIAL_ANALYSIS → Use for strategic decisions, recommendations, comparisons involving specific entities, or calculating strategic/adjusted values for proposals (e.g., "Recommend a tenant", "Calculate strategic value for proposals").
3. GENERAL → Use for conceptual explanations, greetings, or questions about how the business/system works WITHOUT needing specific database rows (e.g., "How does revenue share work?", "Explain yield").

- STRATEGIC CALCULATION (Priority 1): If the query asks to calculate "strategic value", "adjusted value", or "ranking scores" for proposals, it MUST be FINANCIAL_ANALYSIS, even if it uses "Calculate" or "Compute".
- DATA TRUMPS CONCEPT (Priority 2): If the query contains specific entities (e.g., "Starbucks", "Mall A") AND requires their data to be answered, it MUST be FINANCIAL_ANALYSIS/DATA_ANALYSIS.
- VERB OVER NOUN (Priority 3): If the query is conceptual and lacks specific entities, verbs like "Explain", "How", or "Why" take precedence over financial nouns. These questions are GENERAL.
- If the query is a simple retrieval, count, or basic mathematical operation on raw transaction data → DATA_ANALYSIS

Negative Constraints:
- Do NOT classify conceptual questions as FINANCIAL_ANALYSIS just because they mention metrics like "yield" or "revenue share".
- Do NOT classify entity-specific comparisons as GENERAL just because they use "Explain".
- Return ONLY the label (e.g., FINANCIAL_ANALYSIS).

Query: {query}
"""
    safe_query = query[:100].replace("\n", " ") + ("..." if len(query) > 100 else "")
    start_time = time.monotonic()
    
    # Cascade: Routing always uses the FAST model.
    fast_model = os.getenv("FAST_LLM_MODEL")
    
    try:
        response = call_llm([{"role": "user", "content": prompt}], model=fast_model)
        intent = response.strip().upper()
        
        # Enforce strict labels to prevent router breakage.
        valid_intents = ["DATA_ANALYSIS", "FINANCIAL_ANALYSIS", "GENERAL"]
        if intent not in valid_intents:
            intent = "GENERAL"
            source = "fallback"
            reason = "invalid_label"
        else:
            source = "llm"
            reason = None
            
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        with LOCK:
            INTENT_COUNTS[intent] += 1
            
        log_payload = {
            "event": "intent_classification",
            "intent": intent,
            "source": source,
            "model": fast_model,
            "duration_ms": duration_ms,
            "query_preview": safe_query,
            "query_len": len(query)
        }
        if reason: log_payload["reason"] = reason
        
        print(json.dumps(log_payload))
        return intent
        
    except Exception as e:
        # Fallback to GENERAL is safer as it bypasses SQL entirely.
        duration_ms = int((time.monotonic() - start_time) * 1000)
        with LOCK:
            INTENT_COUNTS["GENERAL"] += 1
            
        print(json.dumps({
            "event": "intent_classification",
            "intent": "GENERAL",
            "source": "fallback",
            "reason": f"exception:{str(e)}",
            "model": fast_model,
            "duration_ms": duration_ms,
            "query_preview": safe_query
        }))
        return "GENERAL"

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
