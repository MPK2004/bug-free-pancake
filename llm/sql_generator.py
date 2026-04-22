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

1. AGGREGATION & COMPARISON:
- Use ORDER BY with DESC for "highest/best"
- Join RULE: Always join on 'id' for target tables (e.g., tenants.id, malls.id).
- PROPOSALS columns: id, tenant_id, mall_id, proposed_rent, expected_sales, expected_yield.
- TRANSACTIONS columns: invoice_no, category, total_sales.
- **GROUP BY RULE**: If using SUM(), all other columns in SELECT must be in GROUP BY.

2. PERFORMANCE ANALYSIS:
- To find top categories/demand, use SUM(tr.total_sales) from 'transactions' (tr).

3. CASE HANDLING:
- Mall and Tenant names are in Proper Case (e.g., 'Mall of Istanbul', 'Zara').
- Categories are Proper Case (e.g., 'Clothing', 'Shoes').

4. OUTPUT:
- Return ONLY SQL
- No explanation

GOOD EXAMPLES:

Question: "Which category has highest demand in Mall of Istanbul?"
SQL:
SELECT category, SUM(total_sales) AS total_demand
FROM transactions
WHERE shopping_mall = 'Mall of Istanbul'
GROUP BY category
ORDER BY total_demand DESC
LIMIT 5;

Question: "Compare clothing popularity across all malls"
SQL:
SELECT shopping_mall, SUM(total_sales) AS revenue
FROM transactions
WHERE category = 'Clothing'
GROUP BY shopping_mall
ORDER BY revenue DESC;

Question: "Compare Zara and Nike at Mall of Istanbul based on yield and demand"
SQL:
SELECT t.name, p.expected_yield, ci.priority, (SELECT SUM(total_sales) FROM transactions WHERE shopping_mall = 'Mall of Istanbul' AND category = t.category) AS total_demand
FROM proposals p
JOIN tenants t ON p.tenant_id = t.id
JOIN malls m ON p.mall_id = m.id
LEFT JOIN category_insights ci ON ci.category = t.category
WHERE (t.name = 'Zara' OR t.name = 'Nike') AND m.name = 'Mall of Istanbul';

Question: "Show top 3 proposals by expected yield"
SQL:
SELECT t.name AS tenant, m.name AS mall, p.expected_yield
FROM proposals p
JOIN tenants t ON p.tenant_id = t.id
JOIN malls m ON p.mall_id = m.id
ORDER BY p.expected_yield DESC
LIMIT 3;
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
