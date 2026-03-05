import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB", "featurestore"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            item_id     INTEGER NOT NULL,
            event_type  VARCHAR(10) NOT NULL,
            device      VARCHAR(10),
            ts          TIMESTAMP NOT NULL
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Tables created/verified")
