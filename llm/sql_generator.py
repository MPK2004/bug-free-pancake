import re
from llm.client import call_llm

def generate_sql(user_query, schema_str, mode="analytical"):
    """
    Constructs the prompt and calls the LLM to generate SQL.
    """
    if mode == "strategic":
        instructions = """
1. STRATEGIC MODE:
    - DO NOT use LIMIT 1.
    - MANDATORY: Include `expected_yield`, `demand` (SUM(total_sales)), and `priority` (from category_insights).
    - Aliases: `t` for tenants, `p` for proposals, `tr` for transactions, `ci` for category_insights.
    - Standard join: proposals (p) -> tenants (t) -> malls (m).
    - LEFT JOIN transactions (tr) and category_insights (ci) on category.
"""
    else:
        instructions = """
1. ANALYTICAL MODE:
    - Primary table: `transactions` (alias `tr`).
    - Use `tr.category` and `tr.shopping_mall` for filtering/grouping.
    - Join `category_insights` (ci) ONLY if priority is needed.
    - SQL Rule: COALESCE(MAX(ci.priority), 'UNKNOWN') AS priority.
    - NEVER use alias `t` (tenants) unless explicitly asked for tenant-specific details.
    - Dominance = highest SUM(tr.total_sales) only.
"""

    messages = [
        {"role": "user", "content": f"""
Convert the following natural language query into SQL. 

Schema:
{schema_str}

User Question:
{user_query}

Mode: {mode.upper()}

SCALING RULES:
{instructions}
- If the query involves comparison, ranking, or "highest/lowest" values: DO NOT use LIMIT and DO NOT use ORDER BY. Return all relevant rows without sorting bias for analysis.
- DO NOT compute final metrics (like adjusted values or rankings) in SQL. Return the raw component fields (e.g., expected_yield, total_sales, priority) so the agent can perform the calculation via tools.

3. CASE HANDLING:
- Mall and Tenant names are in Proper Case (e.g., 'Mall of Istanbul', 'Zara').

4. OUTPUT:
- Return ONLY SQL.

GOOD EXAMPLES:

Mode: STRATEGIC
User Question: "Recommend a tenant for Kanyon mall"
SQL:
SELECT t.name AS tenant, p.expected_yield, SUM(tr.total_sales) AS demand, MAX(ci.priority) AS priority
FROM proposals p
JOIN tenants t ON p.tenant_id = t.id
JOIN malls m ON p.mall_id = m.id
LEFT JOIN transactions tr ON tr.category = t.category AND tr.shopping_mall = m.name
LEFT JOIN category_insights ci ON ci.category = t.category
WHERE m.name = 'Kanyon'
GROUP BY t.name, p.expected_yield;

Mode: ANALYTICAL
User Question: "Which category dominates Kanyon?"
SQL:
SELECT tr.category AS dominant_category, SUM(tr.total_sales) AS demand, COALESCE(MAX(ci.priority), 'UNKNOWN') AS priority
FROM transactions tr
LEFT JOIN category_insights ci ON tr.category = ci.category
WHERE tr.shopping_mall = 'Kanyon'
GROUP BY tr.category
ORDER BY demand DESC;
"""}
    ]
    
    response_text = call_llm(messages)
    return parse_sql(response_text)

def parse_sql(sql_query):
    """
    Cleans up the SQL query string returned by the LLM.
    """
    if "```sql" in sql_query:
        sql = sql_query.split("```sql")[1].split("```")[0]
    elif "```" in sql_query:
        sql = sql_query.split("```")[1].split("```")[0]
    else:
        sql = sql_query
        
    # Remove common LLM labels if they leaked into the output
    sql = re.sub(r'^(Mode|User Question|SQL):.*?\n', '', sql, flags=re.MULTILINE | re.IGNORECASE)
    
    # Find the first SELECT statement and use that as the starting point
    select_match = re.search(r'SELECT\s+', sql, re.IGNORECASE)
    if select_match:
        sql = sql[select_match.start():]
        
    sql = sql.replace("SQL:", "").strip()
    sql = re.sub(r'```.*$', '', sql)
    
    sql_lower = sql.lower()
    
    # Fix: If t.category is used but only transactions table is joined
    if "t.category" in sql and ("transactions tr" in sql_lower or "transactions as tr" in sql_lower) and "tenants t" not in sql_lower:
        sql = sql.replace("t.category", "tr.category")
    
    # Fix: Ambiguous 'name' in strategic queries (favor t.name if available)
    if " name" in sql_lower and "tenants t" in sql_lower and " t.name" not in sql:
        sql = sql.replace(" name", " t.name")

    return sql.strip()
