import pandas as pd
from sqlalchemy import create_engine
DB_USER = 'postgres'
DB_PASSWORD = '100724'
DB_HOST = '127.0.0.1'
DB_PORT = '5432'
DB_NAME = 'testdb'
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

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
        try:
            p['proposed_rent'] = float(p.get('proposed_rent', 0))
            p['expected_sales'] = float(p.get('expected_sales', 0))
            p['revenue_share'] = float(p.get('revenue_share', 0))
            
            if p['proposed_rent'] < 0 or p['expected_sales'] < 0 or p['revenue_share'] < 0:
                print(f"[warning] Negative values detected in proposal: {p}", file=sys.stderr)
            
            valid_proposals.append(p)
        except (ValueError, TypeError):
            print(f"[warning] Skipping invalid proposal data: {p}", file=sys.stderr)
            continue

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
    Computes adjusted values using raw strategic metrics: expected_yield, demand, and priority.
    Formula: Adjusted Value = yield * demand * priority_weight
    Priority weights: HIGH=3, MEDIUM=2, LOW=1
    """
    if not proposals_data:
        return []
    
    PRIORITY_WEIGHTS = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    
    results = []
    for p in proposals_data:
        try:
            p_yield = float(p.get('expected_yield', 1))
            p_demand = float(p.get('demand', p.get('total_sales', 0)))
            p_priority = str(p.get('priority', 'LOW')).upper()
            
            weight = PRIORITY_WEIGHTS.get(p_priority, 1)
            adjusted_value = p_yield * p_demand * weight
            
            p['adjusted_value'] = adjusted_value
            results.append(p)
        except (ValueError, TypeError):
            continue
            
    return sorted(results, key=lambda x: x['adjusted_value'], reverse=True)

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