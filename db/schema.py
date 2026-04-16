def get_schema(cursor):
    """
    Retrieves the table names and their respective columns from the public schema.
    """
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
    """
    Formats the schema dictionary into a string for LLM consumption.
    """
    return "\n".join([f"{t}({', '.join(c)})" for t, c in schema_dict.items()])
