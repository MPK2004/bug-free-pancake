import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def run_sql():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5434"),
        database=os.getenv("DB_NAME", "query_data"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "postgres")
    )
    cur = conn.cursor()
    
    try:
        with open('db/init_mall_db.sql', 'r') as f:
            sql = f.read()
            cur.execute(sql)
            conn.commit()
            print("Database initialized successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error initializing database: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_sql()
