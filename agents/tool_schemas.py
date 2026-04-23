FINANCIAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "financial_analysis",
            "description": "Calculates annual rent, expected revenue, and total value for a list of proposals. Use this when you have raw proposal data and need to calculate total values.",
            "parameters": {
                "type": "object",
                "properties": {
                    "proposals_data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "proposed_rent": {"type": "number"},
                                "expected_sales": {"type": "number"},
                                "revenue_share": {"type": "number"},
                                "tenant_id": {"type": "integer"}
                            }
                        },
                        "description": "List of proposals with rent, sales, and revenue share data."
                    }
                },
                "required": ["proposals_data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_proposals",
            "description": "Compares proposals by applying market trend factors and identifies the best one. Use this when you need to find the 'best' proposal or compare them strategically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "proposals_data": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of proposals (optionally already processed by financial_analysis)."
                    },
                    "tenants_data": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of tenant information including category and brand name."
                    }
                },
                "required": ["proposals_data", "tenants_data"]
            }
        }
    }
]
