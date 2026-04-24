from agents import data_analyst, financial_analyst, general_responder
from llm.client import call_llm

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

1. DATA_ANALYSIS → requires database queries (counts, filters, aggregations)
2. FINANCIAL_ANALYSIS → requires calculations, comparisons, or financial metrics
3. GENERAL → general knowledge, greetings, or questions about the system that don't require data.

Rules:
- If query involves numbers, calculations, or comparisons → FINANCIAL_ANALYSIS
- If query involves counting, filtering, or database lookup → DATA_ANALYSIS
- If query is general (e.g., "What is the capital of France?", "Hi", "Explain malls") → GENERAL
- Do NOT explain
- Return ONLY the label (e.g., FINANCIAL_ANALYSIS)

Query: {query}
"""
    try:
        response = call_llm([{"role": "user", "content": prompt}])
        intent = response.strip().upper()
        
        # Enforce strict labels to prevent router breakage. We upper() and strip() 
        # to handle LLM variations (e.g. "General." or "general") while maintaining
        # compatibility with exact string comparisons in the route() function.
        valid_intents = ["DATA_ANALYSIS", "FINANCIAL_ANALYSIS", "GENERAL"]
        if intent not in valid_intents:
            # Fallback to DATA_ANALYSIS as the safest default for mall-related queries.
            # This ensures that if the LLM produces a hallucinated label, the system
            # still attempts to answer the user's question via the standard data layer.
            return "DATA_ANALYSIS"
        return intent
    except Exception:
        # Fallback to DATA_ANALYSIS ensures system continuity even during LLM provider
        # downtime or request timeouts.
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
