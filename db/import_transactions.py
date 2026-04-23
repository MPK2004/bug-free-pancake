import psycopg2
import csv
import os
import time
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5434"),
        database=os.getenv("DB_NAME", "query_data"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "postgres")
    )

def import_transactions():
    conn = get_connection()
    cur = conn.cursor()
    csv_file = "customer_shopping_data (1).csv"
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found.")
        return

    print(f"Starting import of {csv_file}...")
    start_time = time.time()

    try:
        # Use COPY for high performance if possible, or simple executemany
        # COPY is preferred for 100k rows
        with open(csv_file, 'r') as f:
            # Skip header
            next(f)
            # Use copy_from for speed
            # Columns in CSV: invoice_no,customer_id,gender,age,category,quantity,price,payment_method,invoice_date,shopping_mall
            # Columns in Table: invoice_no,customer_id,gender,age,category,quantity,price,payment_method,invoice_date,shopping_mall
            # (total_sales is generated)
            cur.copy_from(f, 'transactions', sep=',', columns=(
                'invoice_no', 'customer_id', 'gender', 'age', 'category', 'quantity', 'price', 'payment_method', 'invoice_date', 'shopping_mall'
            ))

        conn.commit()
        duration = time.time() - start_time
        print(f"Import completed successfully in {duration:.2f} seconds.")

        # Validate row count
        cur.execute("SELECT COUNT(*) FROM transactions;")
        count = cur.fetchone()[0]
        print(f"Total rows imported: {count}")

    except Exception as e:
        conn.rollback()
        print(f"Error importing data: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import_transactions()
