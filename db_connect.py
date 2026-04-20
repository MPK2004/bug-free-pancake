from sqlalchemy import create_engine
import pandas as pd

engine = create_engine(
    "postgresql://postgres:100724@127.0.0.1:5432/testdb"
)

try:
    df = pd.read_sql("SELECT * FROM sales LIMIT 10;", engine)
    print("Connected successfully!\n")
    print(df)
except Exception as e:
    print("Error:", e)