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
    df = pd.DataFrame(proposals_data)
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

TOOL_REGISTRY = {
    "financial_analysis": financial_analysis,
    "compare_proposals": compare_proposals
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