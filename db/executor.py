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

def validate_sql(sql):
    """
    Heuristic validation to catch common SQL generation errors like undefined aliases.
    """
    errors = []
    sql_lower = sql.lower()

    # Alias validation
    if " t." in sql and "tenants t" not in sql_lower and "tenants as t" not in sql_lower:
        errors.append("Alias 't' used without tenants table")

    if " tr." in sql and "transactions tr" not in sql_lower and "transactions as tr" not in sql_lower:
        errors.append("Alias 'tr' used without transactions table")

    if " p." in sql and "proposals p" not in sql_lower and "proposals as p" not in sql_lower:
        errors.append("Alias 'p' used without proposals table")

    return errors

def fix_sql(sql):
    """
    Attempts to auto-correct common SQL errors identified during validation or execution.
    """
    sql_lower = sql.lower()
    
    # If t.category is used but only transactions table is joined (common LLM slip)
    if "t.category" in sql and ("transactions tr" in sql_lower or "transactions as tr" in sql_lower) and "tenants t" not in sql_lower:
        sql = sql.replace("t.category", "tr.category")
    
    # If t.shopping_mall is used but only transactions table is joined
    if "t.shopping_mall" in sql and ("transactions tr" in sql_lower or "transactions as tr" in sql_lower) and "tenants t" not in sql_lower:
        sql = sql.replace("t.shopping_mall", "tr.shopping_mall")

    # Ambiguous 'name' in strategic queries (favor t.name if available)
    if " name" in sql_lower and "tenants t" in sql_lower and " t.name" not in sql:
        sql = sql.replace(" name", " t.name")

    # ILLEGAL JOIN FIX: Catch mall_id = shopping_mall mismatch
    if "mall_id = tr.shopping_mall" in sql_lower or "tr.shopping_mall = p.mall_id" in sql_lower or "tr.shopping_mall = mall_id" in sql_lower:
        if "JOIN malls m" not in sql:
            # Inject malls bridge
            sql = sql.replace("JOIN transactions tr ON p.mall_id = tr.shopping_mall", 
                              "JOIN malls m ON p.mall_id = m.id JOIN transactions tr ON tr.shopping_mall = m.name")
            sql = sql.replace("JOIN transactions tr ON tr.shopping_mall = p.mall_id", 
                              "JOIN malls m ON p.mall_id = m.id JOIN transactions tr ON tr.shopping_mall = m.name")
            sql = sql.replace("JOIN transactions tr ON tr.shopping_mall = mall_id", 
                              "JOIN malls m ON p.mall_id = m.id JOIN transactions tr ON tr.shopping_mall = m.name")

    return sql

def execute_query(cursor, sql, timeout_ms=5000):
    """
    Executes the query with a validation/correction layer and a single retry on specific errors.
    """
    cursor.execute(f"SET statement_timeout = {timeout_ms}")
    
    # 1. Pre-execution validation
    errors = validate_sql(sql)
    if errors:
        sql = fix_sql(sql)

    try:
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        error_str = str(e).lower()
        # 2. Post-execution error handling (e.g., missing FROM-clause)
        if "missing from-clause entry" in error_str or "undefined table" in error_str:
            print(f"SQL Error detected: {e}. Attempting auto-fix...", file=sys.stderr)
            sql = fix_sql(sql)
            try:
                # Need to rollback if transaction was aborted by error
                if cursor.connection:
                    cursor.connection.rollback()
                cursor.execute(f"SET statement_timeout = {timeout_ms}")
                cursor.execute(sql)
                return cursor.fetchall()
            except Exception:
                raise e # If fix fails, raise original error
        raise e
