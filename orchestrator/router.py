from agents import data_analyst, decision_engine, financial_analyst

def route(query, results):
    """
    Decides which agent should handle the query based on rules.
    Returns the agent module.
    """
    q = query.lower()
    
    # Financial Analyst signals: Prioritize these over strategic signals
    # to ensure complex math is handled by tools rather than scored generically.
    financial_signals = ["proposal", "rent", "revenue", "yield", "value", "compare"]
    if any(s in q for s in financial_signals):
        return financial_analyst

    strategic_signals = [
        "recommend", "best", "compare", "should", "which is better",
        "what should", "suggest", "rank", "choice", "choose", "fit"
    ]
    
    if any(s in q for s in strategic_signals):
        return decision_engine
        
    return data_analyst
