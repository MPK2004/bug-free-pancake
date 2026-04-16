from llm.client import call_llm

def generate_sql(user_query, schema_str):
    """
    Constructs the prompt and calls the LLM to generate SQL.
    """
    messages = [
        {"role": "user", "content": f"""
Convert the following natural language query into SQL.

Schema:
{schema_str}

User Question:
{user_query}

IMPORTANT RULES:

1. COMPARISON QUERIES:
- If the question asks "why less", "more", "highest", "lowest", "compare":
  → DO NOT filter to one category
  → Use GROUP BY across all categories
  → Use COUNT(*) for comparison
  → Use ORDER BY to show ranking

2. FILTERING:
- Only use WHERE if user explicitly asks for a specific category

3. CASE HANDLING:
- The dataset uses UPPERCASE values (e.g., 'SCIENCE')
- Always match case exactly OR use UPPER()

4. OUTPUT:
- Return ONLY SQL
- No explanation

GOOD EXAMPLE:
Question: "why science has less numbers"
SQL:
SELECT topic, COUNT(*) AS count
FROM news
GROUP BY topic
ORDER BY count ASC;
"""}
    ]
    
    response_text = call_llm(messages)
    return parse_sql(response_text)

def parse_sql(sql_query):
    """
    Cleans up the SQL query string returned by the LLM.
    """
    if "```sql" in sql_query:
        sql_query = sql_query.split("```sql")[1].split("```")[0]
    elif "```" in sql_query:
        sql_query = sql_query.split("```")[1].split("```")[0]
        
    sql_query = sql_query.replace("SQL:", "").strip()
    return sql_query
