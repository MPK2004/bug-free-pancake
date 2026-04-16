import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    db_config = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("READONLY_DB_USER"),
        "password": os.getenv("READONLY_DB_PASS")
    }
    return psycopg2.connect(**db_config)
