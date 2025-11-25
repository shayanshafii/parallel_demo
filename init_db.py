"""
DATABASE INITIALIZATION HELPER SCRIPT
Run this script to initialize the database table if needed
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def init_database():
    """INITIALIZE DATABASE TABLE"""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is required")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # CREATE TABLE
        cur.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id SERIAL PRIMARY KEY,
                search_id TEXT NOT NULL,
                query TEXT NOT NULL,
                mode TEXT NOT NULL,
                result_url TEXT NOT NULL,
                result_title TEXT,
                is_correct BOOLEAN NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # CREATE INDEXES
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_search_id ON evaluations(search_id)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON evaluations(created_at)
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("SUCCESS: Database initialized successfully")
    
    except Exception as e:
        print(f"ERROR: Failed to initialize database - {str(e)}")

if __name__ == "__main__":
    init_database()

