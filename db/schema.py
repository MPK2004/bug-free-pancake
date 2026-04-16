SCHEMA_METADATA = {
    "news": {
        "description": "Table containing news articles crawled from various domains.",
        "columns": {
            "domain": "The source website of the news article (e.g., cnn.com).",
            "id": "Unique identifier for the article.",
            "link": "Direct URL to the full news article.",
            "lang": "Language code of the article (e.g., 'en' for English).",
            "title": "Headline of the news article.",
            "published_date": "The timestamp when the article was published.",
            "topic": "The category or subject of the news (e.g., 'SCIENCE', 'TECHNOLOGY')."
        }
    }
}

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
    Formats the schema dictionary into an enriched string with descriptions for LLM consumption.
    """
    formatted_tables = []
    for table, columns in schema_dict.items():
        table_info = SCHEMA_METADATA.get(table, {})
        table_desc = table_info.get("description", "No description available.")
        
        column_lines = []
        for col in columns:
            col_desc = table_info.get("columns", {}).get(col, "No description available.")
            column_lines.append(f"  - {col}: {col_desc}")
        
        table_str = f"Table: {table}\nDescription: {table_desc}\nColumns:\n" + "\n".join(column_lines)
        formatted_tables.append(table_str)
    
    return "\n\n".join(formatted_tables)
