from agents import data_analyst, decision_engine

def route(query, results):
    """
    Decides which agent should handle the query based on rules.
    Returns the agent module.
    """
    q = query.lower()
    strategic_signals = [
        "recommend", "best", "compare", "should", "which is better",
        "what should", "suggest", "rank", "choice", "choose", "fit"
    ]
    
    if any(s in q for s in strategic_signals):
        return decision_engine
        
    return data_analyst
