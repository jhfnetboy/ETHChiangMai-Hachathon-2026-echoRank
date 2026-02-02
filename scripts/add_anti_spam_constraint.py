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
    conn.autocommit = True
    with conn.cursor() as cur:
        print("Cleaning up duplicates (keeping latest)...")
        # Removing duplicates based on user_id and activity_id, keeping the one with the highest ID
        cur.execute("""
            DELETE FROM feedbacks a USING feedbacks b
            WHERE a.id < b.id
            AND a.user_id = b.user_id
            AND a.activity_id = b.activity_id;
        """)
        print(f"Duplicates removed. Affected rows: {cur.rowcount}")

        print("Adding UNIQUE constraint...")
        try:
            cur.execute("""
                ALTER TABLE feedbacks 
                ADD CONSTRAINT unique_user_activity UNIQUE (user_id, activity_id);
            """)
            print("Constraint 'unique_user_activity' added successfully.")
        except psycopg2.errors.DuplicateTable:
            print("Constraint already exists.")
        except Exception as e:
            if "already exists" in str(e):
                 print("Constraint already exists (caught via Exception).")
            else:
                 print(f"Error adding constraint: {e}")

    conn.close()
    print("Done.")
except Exception as e:
    print(f"Fatal Error: {e}")
