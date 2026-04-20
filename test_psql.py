import pandas as pd
from sqlalchemy import create_engine
import os
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '100724')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'testdb')
TABLE_NAME = 'sales'
try:
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    df = pd.read_sql(f'SELECT * FROM {TABLE_NAME} LIMIT 10;', engine)
    print('Connected successfully!\n')
    print(df)
except Exception as e:
    print(f' Database connection failed: {e}')
    df = None

def extract_schema(engine, table_name):
    query = '\n    SELECT column_name, data_type\n    FROM information_schema.columns\n    WHERE table_name = %s;\n    '
    schema_df = pd.read_sql(query, engine, params=(table_name,))
    schema = []
    for _, row in schema_df.iterrows():
        schema.append({'column': row['column_name'], 'type': row['data_type'], 'description': f'{row['column_name']} field from {table_name}'})
    return schema

def data_analyst_agent(df):
    return {'rows': len(df), 'columns': list(df.columns), 'missing_values': df.isnull().sum().to_dict()}

def financial_analyst_agent(df):
    insights = {}
    if 'price' in df.columns:
        insights['avg_price'] = df['price'].mean()
        insights['max_price'] = df['price'].max()
        insights['total_revenue'] = (df['price'] * df['quantity']).sum()
    return insights

def business_agent(financial_output):
    if financial_output.get('avg_price', 0) > 1000:
        return 'Focus on premium customers'
    else:
        return 'Increase marketing for mass customers'

def run_pipeline(engine, table_name):
    try:
        df = pd.read_sql(f'SELECT * FROM {table_name};', engine)
    except Exception as e:
        print(f' Error reading table {table_name}: {e}')
        return None
    schema = extract_schema(engine, table_name)
    data_summary = data_analyst_agent(df)
    financial = financial_analyst_agent(df)
    decision = business_agent(financial)
    return {'schema': schema, 'data_summary': data_summary, 'financial': financial, 'decision': decision}
if df is not None:
    result = run_pipeline(engine, TABLE_NAME)
    print('\nFINAL OUTPUT:')
    print(result)
else:
    print(' Skipping pipeline: No database connection available.')