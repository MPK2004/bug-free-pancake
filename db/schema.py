import json
import os

def load_domain_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'domain_config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading domain config: {e}")
        return {}

DOMAIN_CONFIG = load_domain_config()
SCHEMA_METADATA = DOMAIN_CONFIG.get("schema_metadata", {})

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

def get_table_summaries():
    """
    Returns a lightweight summary of all tables (names, descriptions, relationships) 
    for the Step 1 Table Selection process.
    """
    summaries = []
    for table, info in SCHEMA_METADATA.items():
        summary = {
            "table": table,
            "description": info.get("description", "No description available."),
            "relationships": info.get("relationships", "No relationship data available.")
        }
        summaries.append(summary)
    return summaries

def format_schema(schema_dict, selected_tables=None):
    """
    Formats the schema dictionary into an enriched string.
    If selected_tables is provided, it only includes those tables (Schema Pruning).
    """
    formatted_tables = []
    for table, columns in schema_dict.items():
        if selected_tables and table not in selected_tables:
            continue
            
        table_info = SCHEMA_METADATA.get(table, {})
        table_desc = table_info.get("description", "No description available.")
        table_rel = table_info.get("relationships", "No relationship data available.")
        
        column_lines = []
        for col in columns:
            col_desc = table_info.get("columns", {}).get(col, "No description available.")
            column_lines.append(f"  - {col}: {col_desc}")
        
        table_str = f"Table: {table}\nDescription: {table_desc}\nRelationships: {table_rel}\nColumns:\n" + "\n".join(column_lines)
        formatted_tables.append(table_str)
    
    return "\n\n".join(formatted_tables)
