import re
import json
from llm.client import call_llm
from db.schema import DOMAIN_CONFIG, get_table_summaries, format_schema

def select_relevant_tables(user_query, mode="analytical", model=None):
    """
    Step 1: Fast LLM identifies relevant tables based on summaries and relationships.
    Ensures intermediate join tables are selected via relationship metadata.
    """
    summaries = get_table_summaries()
    summaries_str = json.dumps(summaries, indent=2)
    
    config = (DOMAIN_CONFIG or {}).get("sql_generation", {}).get(mode, {})
    mode_instructions = config.get("instructions", "")
    
    prompt = f"""
Given the following database tables and their relationships, identify the tables needed to answer the user's query.

MODE INSTRUCTIONS (Pay attention to required metrics):
{mode_instructions}

STRICT RULES:
1. Identify all tables explicitly mentioned or related to the query.
2. MANDATORY: Include intermediate tables required for JOIN paths. If Table A and Table B are needed but don't connect directly, you MUST include the linking table(s) defined in the 'relationships' field.
3. If the instructions require metrics like 'demand', ensure you include the 'transactions' table.
4. Return only a JSON array of table names.

Tables:
{summaries_str}

User Query: "{user_query}"

Response format: ["table1", "table2"]
"""
    messages = [{"role": "user", "content": prompt}]
    response = call_llm(messages, model=model)
    
    try:
        # Extract JSON array from response
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
    except:
        return []

def generate_sql(user_query, schema_data, history=None, mode="analytical", model=None, feedback=None):
    """
    Constructs the prompt and calls the LLM to generate SQL.
    If schema_data is a dict (raw schema), it performs dynamic pruning.
    If it's a string, it uses it directly (legacy support).
    """
    # Dynamic Schema Pruning
    selected_tables = None
    if isinstance(schema_data, dict):
        # Only prune if there are many tables (e.g., > 4 for this small demo, or 10+ for real world)
        if len(schema_data) > 4:
            print(f"[sql_generator] Large schema detected ({len(schema_data)} tables). Pruning...")
            selected_tables = select_relevant_tables(user_query, mode=mode, model=model)
            print(f"[sql_generator] Selected tables: {selected_tables}")
        
        schema_str = format_schema(schema_data, selected_tables=selected_tables)
    else:
        schema_str = schema_data
    config = (DOMAIN_CONFIG or {}).get("sql_generation", {}).get(mode, {})
    instructions = config.get("instructions", "No instructions provided for this mode.")
    examples = config.get("examples", [])
    
    example_str = ""
    for ex in examples:
        example_str += f"\nMode: {ex.get('mode')}\nUser Question: \"{ex.get('question')}\"\nSQL:\n{ex.get('sql')}\n"

    history_str = ""
    if history:
        history_str = "### CONTEXT HISTORY (Pronoun Resolution) ###\n"
        for msg in history:
            history_str += f"{msg['role'].upper()}: {msg['content']}\n"
        history_str += "\n"

    feedback_str = ""
    if feedback:
        feedback_str = f"""
### PREVIOUS ATTEMPT FAILED ###
The following SQL was generated but failed execution:
{feedback.get('previous_sql', '')}

ERROR COMPLAINT:
{feedback.get('error', '')}

FIX THE ERROR above and return the corrected SQL. Pay attention to scoping, table aliases, and column names.
"""

    messages = [
        {"role": "system", "content": "You are an expert SQL generator. Use the context history to resolve pronouns like 'they', 'it', or 'previous'. If provided with feedback, fix the error in the previous query."},
        {"role": "user", "content": f"""
{history_str}
{feedback_str}
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
{example_str}
"""}
    ]
    
    response_text = call_llm(messages, model=model)
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
