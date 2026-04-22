from llm.client import call_llm

def generate_sql(user_query, schema_str):
    """
    Constructs the prompt and calls the LLM to generate SQL.
    """
    messages = [
        {"role": "user", "content": f"""
Convert the following natural language query into SQL for a mall leasing business intelligence system.

Schema:
{schema_str}

User Question:
{user_query}

IMPORTANT RULES:

1. STRATEGIC vs LOOKUP QUERIES:
- **Strategic Queries** (e.g., "Which is the best fit?", "What do you recommend?", "Compare X and Y"):
    - DO NOT use LIMIT 1. The decision engine needs all candidates to score them.
    - HARD RULE: You MUST include `expected_yield`, `demand` (SUM of total_sales), and `priority` (from category_insights).
    - Queries that only return names for strategic questions are INVALID.
- **Lookup Queries** (e.g., "Show top 3", "Who has highest yield?"):
    - Use LIMIT and ORDER BY as requested.

2. AGGREGATION & JOINS (FOR STRATEGIC QUERIES):
- Always join `proposals` (p) with `tenants` (t) on `tenant_id`.
- Always join `malls` (m) on `mall_id`.
- Always LEFT JOIN `transactions` (tr) on `category` AND `shopping_mall` to get demand.
- Always LEFT JOIN `category_insights` (ci) on `category` to get strategic priority.
- Standardize naming: Always use `t.name AS tenant`.
- **GROUP BY**: You must GROUP BY all non-aggregated columns.

3. PERFORMANCE ANALYSIS:
- Demand = SUM(tr.total_sales) from `transactions`.

4. CASE HANDLING:
- Mall and Tenant names are in Proper Case (e.g., 'Mall of Istanbul', 'Zara').

5. OUTPUT:
- Return ONLY SQL.

GOOD EXAMPLES:

User Question: "Recommend a tenant for Kanyon mall"
SQL:
SELECT 
    t.name AS tenant,
    p.expected_yield,
    SUM(tr.total_sales) AS demand,
    MAX(ci.priority) AS priority
FROM proposals p
JOIN tenants t ON p.tenant_id = t.id
JOIN malls m ON p.mall_id = m.id
LEFT JOIN transactions tr 
    ON tr.category = t.category 
    AND tr.shopping_mall = m.name
LEFT JOIN category_insights ci 
    ON ci.category = t.category
WHERE m.name = 'Kanyon'
GROUP BY t.name, p.expected_yield;

User Question: "Compare Zara and Nike at Mall of Istanbul. Which is better?"
SQL:
SELECT 
    t.name AS tenant, 
    p.expected_yield, 
    SUM(tr.total_sales) AS demand,
    MAX(ci.priority) AS priority
FROM proposals p
JOIN tenants t ON p.tenant_id = t.id
JOIN malls m ON p.mall_id = m.id
LEFT JOIN transactions tr 
    ON tr.category = t.category 
    AND tr.shopping_mall = m.name
LEFT JOIN category_insights ci 
    ON ci.category = t.category
WHERE (t.name = 'Zara' OR t.name = 'Nike') AND m.name = 'Mall of Istanbul'
GROUP BY t.name, p.expected_yield;
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
