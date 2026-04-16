from llm.client import call_llm

def analyze_results(user_query, results, cursor_description):
    """
    Analyzes SQL results and provides a natural language summary.
    """
    if not results:
        return "No data found to analyze."

    columns = [desc[0] for desc in cursor_description]
    formatted_data = "\n".join(
        [", ".join([f"{col}: {val}" for col, val in zip(columns, row)]) for row in results]
    )

    analysis_prompt = f"""
You are answering a user question using SQL query results.

User Question:
{user_query}

Data:
{formatted_data}

RULES:
- Answer the user's question directly
- Use the data to support your answer
- Do NOT invent external reasons
- If the question asks "why", explain based ONLY on visible data patterns
- If true cause cannot be determined, clearly say so

OUTPUT:
- 2 to 4 bullet points
"""

    messages = [{"role": "user", "content": analysis_prompt}]
    return call_llm(messages)
