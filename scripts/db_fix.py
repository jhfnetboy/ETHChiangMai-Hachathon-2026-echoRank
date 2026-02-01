import os
import psycopg2
from dotenv import load_dotenv

# Load env from services/bot/.env
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/bot/.env'))
load_dotenv(env_path)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "")
DB_NAME = os.getenv("POSTGRES_DB", "echorank_crawler")

print(f"Connecting to {DB_NAME} as {DB_USER}...")

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME
    )
    with conn.cursor() as cur:
        # Check existing tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print("Existing tables:", [t[0] for t in tables])

        # Explicitly create user_wallets
        print("Creating user_wallets table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_wallets (
                user_id TEXT PRIMARY KEY,
                wallet_address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("Table creation committed.")

        # Check again
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print("Existing tables after creation:", [t[0] for t in tables])

    conn.close()
except Exception as e:
    print(f"Error: {e}")
