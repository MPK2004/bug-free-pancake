import pandas as pd
import ast
import operator
import math
from sqlalchemy import create_engine
from db.schema import DOMAIN_CONFIG

class SafeEvaluator:
    """
    A secure mathematical expression evaluator using AST.
    Avoids eval() to prevent RCE vulnerabilities.
    """
    def __init__(self):
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg
        }
        self.functions = {
            'log': math.log,
            'sqrt': math.sqrt,
            'max': max,
            'min': min
        }

    def evaluate(self, expression, context):
        """
        Parses and evaluates a math string safely.
        """
        try:
            node = ast.parse(expression, mode='eval').body
            return self._eval(node, context)
        except Exception as e:
            raise ValueError(f"Invalid or unsafe expression: {expression}. Error: {e}")

    def _eval(self, node, context):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant): # Python 3.8+
            return node.value
        elif isinstance(node, ast.BinOp):
            return self.operators[type(node.op)](self._eval(node.left, context), self._eval(node.right, context))
        elif isinstance(node, ast.UnaryOp):
            return self.operators[type(node.op)](self._eval(node.operand, context))
        elif isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            raise NameError(f"Variable '{node.id}' not allowed in this context.")
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name in self.functions:
                args = [self._eval(arg, context) for arg in node.args]
                return self.functions[func_name](*args)
            raise NameError(f"Function '{func_name}' is not whitelisted.")
        else:
            raise TypeError(f"Unsupported AST node: {type(node)}")

DB_USER = 'postgres'
DB_PASSWORD = '100724'
DB_HOST = '127.0.0.1'
DB_PORT = '5432'
DB_NAME = 'testdb'
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

def safe_float(value, default=0.0):
    """
    Defensively converts a value to float. 
    Returns default if value is None, empty string, or non-numeric.
    """
    if value is None:
        return default
    try:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
        return float(value)
    except (ValueError, TypeError):
        return default

def load_data():
    tenants = pd.read_sql('SELECT * FROM tenants;', engine)
    proposals = pd.read_sql('SELECT * FROM proposals;', engine)
    return (tenants, proposals)

def financial_analysis(proposals_data: list) -> list:
    """
    Calculates annual rent, expected revenue, and total value for a list of proposals.
    """
    if not proposals_data:
        return []
        
    # Input Validation: Type and Range Checks
    valid_proposals = []
    for p in proposals_data:
        # Use safe_float to prevent TypeError: float(None)
        p['proposed_rent'] = safe_float(p.get('proposed_rent'), 0.0)
        p['expected_sales'] = safe_float(p.get('expected_sales'), 0.0)
        p['revenue_share'] = safe_float(p.get('revenue_share'), 0.0)
        
        if p['proposed_rent'] < 0 or p['expected_sales'] < 0 or p['revenue_share'] < 0:
            print(f"[warning] Negative values detected in proposal: {p}", file=sys.stderr)
        
        valid_proposals.append(p)

    if not valid_proposals:
        return []

    df = pd.DataFrame(valid_proposals)
    df['annual_rent'] = df['proposed_rent'] * 12
    df['expected_revenue'] = df['expected_sales'] * (df['revenue_share'] / 100)
    df['total_value'] = df['annual_rent'] + df['expected_revenue']
    return df.to_dict('records')

def market_trends():
    return {'fashion': 'growing', 'fnb': 'high', 'electronics': 'stable'}

def simulate_impact(category):
    impact = {'fashion': 1.2, 'fnb': 1.3, 'electronics': 1.1}
    return impact.get(category, 1)

def compare_proposals(proposals_data: list, tenants_data: list) -> dict:
    """
    Compares proposals by applying market trend factors and identifies the best one.
    """
    if not proposals_data or not tenants_data:
        return {"error": "Missing data for comparison"}
        
    proposals = pd.DataFrame(proposals_data)
    tenants = pd.DataFrame(tenants_data)
    
    # Ensure financial analysis is done
    if 'total_value' not in proposals.columns:
        proposals = pd.DataFrame(financial_analysis(proposals_data))
        
    results = []
    trends = market_trends()
    for _, row in proposals.iterrows():
        tenant_match = tenants[tenants['tenant_id'] == row['tenant_id']]
        if tenant_match.empty:
            continue
        tenant = tenant_match.iloc[0]
        category = tenant['category']
        trend = trends.get(category, 'stable')
        factor = simulate_impact(category)
        adjusted_value = row['total_value'] * factor
        results.append({
            'brand': tenant['brand_name'], 
            'category': category, 
            'base_value': float(row['total_value']), 
            'trend': trend, 
            'adjusted_value': float(adjusted_value)
        })
    
    if not results:
        return {"error": "No matching tenants found for proposals"}
        
    result_df = pd.DataFrame(results)
    best = result_df.loc[result_df['adjusted_value'].idxmax()].to_dict()
    return {
        "all_proposals": result_df.to_dict('records'),
        "best_proposal": best
    }

def calculate_adjusted_value(proposals_data: list) -> list:
    """
    Computes adjusted values using raw strategic metrics from the 'metrics' dictionary.
    Identity Preservation: Returns 'entity_identifier'.
    Logic is driven by DOMAIN_CONFIG.
    """
    if not proposals_data:
        return []
    
    tool_config = DOMAIN_CONFIG.get("tools", {}).get("calculate_adjusted_value", {})
    priority_weights = tool_config.get("priority_weights", {})
    default_priority = tool_config.get("default_priority", "LOW")
    formula = tool_config.get("formula", "expected_yield * demand * priority_weight")
    
    evaluator = SafeEvaluator()
    results = []
    for p in proposals_data:
        identifier = p.get('entity_identifier', 'Unknown Entity')
        metrics = p.get('metrics', {})
        
        # Extract metrics based on config
        p_yield = safe_float(metrics.get('expected_yield', metrics.get('yield')), 1.0)
        p_demand = safe_float(metrics.get('demand', metrics.get('total_sales')), 0.0)
        p_priority = str(metrics.get('priority', default_priority)).upper()
        
        weight = priority_weights.get(p_priority, 1)
        
        # Build evaluation context
        context = {
            'expected_yield': p_yield,
            'yield': p_yield,
            'demand': p_demand,
            'total_sales': p_demand,
            'priority_weight': weight,
            'weight': weight
        }
        
        try:
            adjusted_value = evaluator.evaluate(formula, context)
            
            results.append({
                'entity_identifier': identifier,
                'metrics': metrics,
                'status': 'success',
                'adjusted_value': float(adjusted_value)
            })
        except Exception as e:
            results.append({
                'entity_identifier': identifier,
                'metrics': metrics,
                'status': 'failed',
                'error': f"Formula evaluation failed: {e}"
            })
            
    return sorted(results, key=lambda x: x.get('adjusted_value', -1.0), reverse=True)


TOOL_REGISTRY = {
    "financial_analysis": financial_analysis,
    "compare_proposals": compare_proposals,
    "calculate_adjusted_value": calculate_adjusted_value
}

def run():
    tenants, proposals = load_data()
    # Convert DataFrames to list of dicts for the refactored functions
    proposals_list = proposals.to_dict('records')
    tenants_list = tenants.to_dict('records')
    
    analyzed_proposals = financial_analysis(proposals_list)
    comparison = compare_proposals(analyzed_proposals, tenants_list)
    
    if "error" in comparison:
        print(f"Error: {comparison['error']}")
        return

    print('\nAll proposals')
    print(pd.DataFrame(comparison['all_proposals']))
    print('\nBest proposal')
    print(comparison['best_proposal'])
    print('\nRecommendation')
    print('Choose', comparison['best_proposal']['brand'], 'from category', comparison['best_proposal']['category'])
if __name__ == '__main__':
    run()