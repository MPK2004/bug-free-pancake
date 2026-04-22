SCHEMA_METADATA = {
    "malls": {
        "description": "Table containing information about different shopping malls.",
        "columns": {
            "id": "Unique identifier for the mall.",
            "name": "The official name of the shopping mall (e.g., 'Mall of Istanbul')."
        }
    },
    "tenants": {
        "description": "Table containing information about different retail tenants/brands.",
        "columns": {
            "id": "Unique identifier for the tenant.",
            "name": "The name of the brand or store (e.g., 'Zara').",
            "category": "The industry category of the tenant (e.g., 'Clothing', 'Electronics').",
            "brand_type": "The market segment of the brand (e.g., 'Premium', 'Mass')."
        }
    },
    "rental_agreements": {
        "description": "Table tracking active lease agreements between tenants and malls.",
        "columns": {
            "id": "Unique identifier for the agreement.",
            "tenant_id": "Foreign key to the tenants table.",
            "mall_id": "Foreign key to the malls table.",
            "base_rent": "Monthly base rent amount.",
            "revenue_share_percentage": "Percentage of revenue shared with the mall.",
            "start_date": "Commencement date of the lease.",
            "end_date": "Expiry date of the lease.",
            "status": "Current status of the agreement (e.g., 'Active')."
        }
    },
    "proposals": {
        "description": "Table containing new business proposals mapping tenants to malls.",
        "columns": {
            "id": "Unique identifier for the proposal.",
            "tenant_id": "Foreign key to the tenants table.",
            "mall_id": "Foreign key to the malls table.",
            "proposed_rent": "The rent amount being proposed.",
            "expected_sales": "The projected monthly sales for this location.",
            "expected_yield": "The calculated financial yield for this proposal (high is better)."
        }
    },
    "category_insights": {
        "description": "Table containing high-level strategic demand rules and priorities (soft bias).",
        "columns": {
            "category": "The category name (Primary Key).",
            "priority": "Strategic status (HIGH/MEDIUM/LOW).",
            "note": "A business-level guideline explaining the category's strategic importance."
        }
    },
    "transactions": {
        "description": "The ground truth transaction data. IMPORTANT: This table contains the 'category' as a TEXT column. There is NO 'categories' table. Use this for all real demand, sales, and popularity analysis.",
        "columns": {
            "invoice_no": "Unique identifier for the transaction.",
            "customer_id": "Unique identifier for the customer.",
            "gender": "Gender of the customer.",
            "age": "Age of the customer.",
            "category": "Industry category (TEXT, e.g., 'Clothing'). Use this directly for GROUP BY.",
            "quantity": "Number of items purchased.",
            "price": "Price per item.",
            "payment_method": "Method used for payment.",
            "invoice_date": "Date of transaction (YYYY-MM-DD format as text).",
            "shopping_mall": "The mall where transaction occurred (join with malls.name).",
            "total_sales": "Calculated field (quantity * price). SUM this for demand analysis."
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
