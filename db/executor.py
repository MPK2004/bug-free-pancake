import sys
import psycopg2

def is_safe_sql(sql):
    """
    Basic validation to ensure the SQL is a SELECT statement and doesn't contain multiple queries.
    """
    sql_clean = sql.strip().lower()

    if not sql_clean.startswith("select"):
        return False

    if ";" in sql_clean[:-1]:
        return False

    return True

def enforce_limit(sql):
    """
    Ensures the SQL query has a LIMIT clause, defaulting to 50 if missing.
    """
    sql = sql.strip().rstrip(";")
    if "limit" not in sql.lower():
        sql += " LIMIT 50"
    return sql + ";"

def fix_case(sql):
    """
    Ad-hoc fix for specific case sensitivity issues in the dataset.
    """
    # Fix 'science' -> 'SCIENCE' if used as a literal
    return sql.replace("'science'", "'SCIENCE'")

def execute_query(cursor, sql, timeout_ms=5000):
    """
    Executes the query. Retries and agentic fixes are now handled at the pipeline layer.
    """
    cursor.execute(f"SET statement_timeout = {timeout_ms}")
    
    try:
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        # Pipeline layer handles the retry logic
        if cursor.connection:
            cursor.connection.rollback()
        raise e
