# DEPRECATED: This file will be removed after test coverage is implemented. This script will be removed in future releases. Do not extend.
import requests
import psycopg2
import os
from dotenv import load_dotenv
from agents.data_analyst import analyze

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("READONLY_DB_USER"),
    "password": os.getenv("READONLY_DB_PASS")
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json"
}

def is_safe_sql(sql):
    sql_clean = sql.strip().lower()

    if not sql_clean.startswith("select"):
        return False

    if ";" in sql_clean[:-1]:
        return False

    return True

def enforce_limit(sql):
    sql = sql.strip().rstrip(";")
    if "limit" not in sql.lower():
        sql += " LIMIT 50"
    return sql + ";"

def get_schema(cursor):
    cursor.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    rows = cursor.fetchall()

    schema = {}
    for table, column in rows:
        schema.setdefault(table, []).append(column)

    return schema

def format_schema(schema_dict):
    return "\n".join([f"{t}({', '.join(c)})" for t, c in schema_dict.items()])


user_query = input("Enter your question: ")

schema = format_schema(get_schema(cursor))

data = {
    "model": "openai/gpt-3.5-turbo",
    "messages": [
        {"role": "user", "content": f"""
Convert the following natural language query into SQL.

Schema:
{schema}

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
}

response = requests.post(url, headers=headers, json=data)
sql_query = response.json()["choices"][0]["message"]["content"]

if "```sql" in sql_query:
    sql_query = sql_query.split("```sql")[1].split("```")[0]
elif "```" in sql_query:
    sql_query = sql_query.split("```")[1].split("```")[0]
    
sql_query = sql_query.replace("SQL:", "").strip()

print("\nGenerated SQL:", sql_query)
def fix_case(sql):
    return sql.replace("'science'", "'SCIENCE'")

# sql_query = fix_case(sql_query) # commented out to see if it works without manual fix now
final_sql = enforce_limit(sql_query)

print("Executing SQL:", final_sql)
cursor.execute("SET statement_timeout = 5000")
cursor.execute(final_sql)

results = cursor.fetchall()

print("\nResults:")
for row in results:
    print(row)

# Centralized Analysis
columns = [desc[0] for desc in cursor.description]
rows_list = [dict(zip(columns, row)) for row in results]

analysis_context = {
    "user_query": user_query,
    "data": rows_list
}

result = analyze(analysis_context)

print("\nANALYSIS:")
if result["status"] == "success":
    for i, insight in enumerate(result["insights"], 1):
        print(f"{i}. {insight}")
    if "meta" in result:
        print(f"(Rows analyzed: {result['meta']['rows_used']})")
else:
    print(f"Error: {result.get('message', 'Unknown error')}")

conn.close()
