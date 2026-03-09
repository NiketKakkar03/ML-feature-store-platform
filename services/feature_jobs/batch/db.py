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

def create_feature_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_features (
            user_id     INTEGER PRIMARY KEY,
            views_7d    INTEGER DEFAULT 0,
            clicks_7d   INTEGER DEFAULT 0,
            ctr_7d      FLOAT DEFAULT 0.0,
            views_1h    INTEGER DEFAULT 0,
            updated_at  TIMESTAMP DEFAULT NOW()
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_features (
            item_id     INTEGER PRIMARY KEY,
            views_7d    INTEGER DEFAULT 0,
            clicks_7d   INTEGER DEFAULT 0,
            ctr_7d      FLOAT DEFAULT 0.0,
            updated_at  TIMESTAMP DEFAULT NOW()
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Feature tables created/verified")
