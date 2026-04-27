import time
import json
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

    Strict Rules:
    - Return ONLY the label.
    - No punctuation, no explanation.
    """
    prompt = f"""
Classify the user's query into ONE of the following categories:

1. DATA_ANALYSIS → Use for specific data lookups, counting, or filtering (e.g., "How many transactions?").
2. FINANCIAL_ANALYSIS → Use for strategic decisions, recommendations, or comparisons involving specific entities (e.g., "Recommend a tenant", "Compare Starbucks and Zara").
3. GENERAL → Use for conceptual explanations, greetings, or questions about how the business/system works WITHOUT needing specific database rows (e.g., "How does revenue share work?", "Explain yield").

Hierarchy & Routing Rules:
- DATA TRUMPS CONCEPT (Priority 1): If the query contains specific entities (e.g., "Starbucks", "Mall A") AND requires their data to be answered, it MUST be FINANCIAL_ANALYSIS/DATA_ANALYSIS, even if it uses "Explain" or "Why" (e.g., "Explain why Zara has better sales than Nike").
- VERB OVER NOUN (Priority 2): If the query is conceptual and lacks specific entities, verbs like "Explain", "How", or "Why" take precedence over financial nouns. These questions are GENERAL (e.g., "Explain what yield means").
- If the query is a simple retrieval or count of data → DATA_ANALYSIS

Negative Constraints:
- Do NOT classify conceptual questions as FINANCIAL_ANALYSIS just because they mention metrics like "yield" or "revenue share".
- Do NOT classify entity-specific comparisons as GENERAL just because they use "Explain".
- Return ONLY the label (e.g., FINANCIAL_ANALYSIS).

Query: {query}
"""
    safe_query = query[:100].replace("\n", " ") + ("..." if len(query) > 100 else "")
    start_time = time.monotonic()
    
    try:
        response = call_llm([{"role": "user", "content": prompt}])
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
