from agents import data_analyst

def route(query, results):
    """
    Decides which agent should handle the query based on rules.
    Returns the agent module.
    """
    query_lower = query.lower()
    
    if "trend" in query_lower or "compare" in query_lower:
         return data_analyst
        
    return data_analyst
