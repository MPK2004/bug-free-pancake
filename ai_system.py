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

def financial_analysis(proposals):
    proposals['annual_rent'] = proposals['proposed_rent'] * 12
    proposals['expected_revenue'] = proposals['expected_sales'] * (proposals['revenue_share'] / 100)
    proposals['total_value'] = proposals['annual_rent'] + proposals['expected_revenue']
    return proposals

def market_trends():
    return {'fashion': 'growing', 'fnb': 'high', 'electronics': 'stable'}

def simulate_impact(category):
    impact = {'fashion': 1.2, 'fnb': 1.3, 'electronics': 1.1}
    return impact.get(category, 1)

def compare_proposals(proposals, tenants):
    results = []
    trends = market_trends()
    for _, row in proposals.iterrows():
        tenant = tenants[tenants['tenant_id'] == row['tenant_id']].iloc[0]
        category = tenant['category']
        trend = trends.get(category, 'stable')
        factor = simulate_impact(category)
        adjusted_value = row['total_value'] * factor
        results.append({'brand': tenant['brand_name'], 'category': category, 'base_value': row['total_value'], 'trend': trend, 'adjusted_value': adjusted_value})
    result_df = pd.DataFrame(results)
    best = result_df.loc[result_df['adjusted_value'].idxmax()]
    return (result_df, best)

def run():
    tenants, proposals = load_data()
    proposals = financial_analysis(proposals)
    result_df, best = compare_proposals(proposals, tenants)
    print('\nAll proposals')
    print(result_df)
    print('\nBest proposal')
    print(best)
    print('\nRecommendation')
    print('Choose', best['brand'], 'from category', best['category'])
if __name__ == '__main__':
    run()