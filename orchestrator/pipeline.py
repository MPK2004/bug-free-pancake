from db.connection import get_db_connection
from db.schema import get_schema, format_schema
from db.executor import is_safe_sql, enforce_limit, fix_case, execute_query
from llm.sql_generator import generate_sql
from agents.data_analyst import analyze_results

def run_pipeline(user_query):
    """
    Orchestrates the NL-to-SQL-to-Analysis pipeline.
    """
    # 1. Database Connection
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 2. Schema Retrieval
        schema_dict = get_schema(cursor)
        schema_str = format_schema(schema_dict)

        # 3. SQL Generation
        sql_query = generate_sql(user_query, schema_str)
        print(f"\nGenerated SQL: {sql_query}")

        # 4. SQL Refinement & Safety Checks
        sql_query = fix_case(sql_query)
        final_sql = enforce_limit(sql_query)

        if not is_safe_sql(final_sql):
            print("Error: Generated SQL is not safe.")
            return

        print(f"Executing SQL: {final_sql}")

        # 5. Execution
        results = execute_query(cursor, final_sql)

        print("\nResults:")
        for row in results:
            print(row)

        # 6. Analysis
        analysis = analyze_results(user_query, results, cursor.description)
        print("\nANALYSIS:")
        print(analysis)

        return analysis

    finally:
        conn.close()
