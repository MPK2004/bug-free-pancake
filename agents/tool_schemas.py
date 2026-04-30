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
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_adjusted_value",
            "description": "Computes adjusted values using raw strategic metrics. Use this for ranking entities based on domain-specific metrics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "proposals_data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity_identifier": {"type": "string", "description": "The unique name or ID of the entity being evaluated."},
                                "metrics": {
                                    "type": "object",
                                    "description": "Dictionary of raw metrics (e.g., yield, demand, priority) required for the calculation.",
                                    "additionalProperties": {"type": ["number", "string"]}
                                }
                            },
                            "required": ["entity_identifier", "metrics"]
                        },
                        "description": "List of proposals with raw strategic metrics."
                    }
                },
                "required": ["proposals_data"]
            }
        }
    }

]
