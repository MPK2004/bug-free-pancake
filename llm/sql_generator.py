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
- SCHEMA INTELLIGENCE (JOINS):
    - proposals.mall_id MUST be joined with malls.id.
    - transactions.shopping_mall MUST be joined with malls.name.
    - JOIN proposals with transactions via malls: proposals p JOIN malls m ON p.mall_id = m.id JOIN transactions tr ON tr.shopping_mall = m.name.
- TYPE SAFETY: NEVER compare numeric fields with strings. expected_yield is NUMERIC: HIGH > 4, MEDIUM = 2-4, LOW < 2.
- SEMANTIC INTELLIGENCE (RELATIVE SCALING):
    - "Low" / "Poor" / "High" metrics should be relative. Use subqueries to compare against averages.
    - AGGREGATION CONSISTENCY: Always compare metrics at the same level. If the left side is SUM(total_sales) per proposal, the right side average MUST be an average of those sums (e.g., SELECT AVG(total_demand) FROM (SELECT SUM(...) GROUP BY ...)).
    - NEVER use arbitrary constants (e.g., < 2) for qualitative terms.
- FILTERING CONTEXT (WHERE vs HAVING):
    - Use WHERE for row-level filters (e.g., p.mall_id = 1).
    - Use HAVING for filters on aggregated results like SUM(total_sales) or COUNT(*). Demand is an aggregation.
- REASONING SEPARATION: For "Why" or "Explain" queries, return the raw dataset and do NOT add complex SQL filtering logic.

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

    # VALIDATION LAYER: Catch and fix illegal joins
    if "mall_id = tr.shopping_mall" in sql or "tr.shopping_mall = p.mall_id" in sql:
        # Auto-fix: Inject malls bridge if missing
        if "JOIN malls m" not in sql:
            sql = sql.replace("JOIN transactions tr ON p.mall_id = tr.shopping_mall", 
                              "JOIN malls m ON p.mall_id = m.id JOIN transactions tr ON tr.shopping_mall = m.name")
            sql = sql.replace("JOIN transactions tr ON tr.shopping_mall = p.mall_id", 
                              "JOIN malls m ON p.mall_id = m.id JOIN transactions tr ON tr.shopping_mall = m.name")

    return sql.strip()
