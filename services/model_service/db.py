import os
import psycopg


DB_CONFIG = {
    "host": os.getenv("PGHOST", "postgres"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "featurestore"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "postgres"),
}


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS inference_events (
    id BIGSERIAL PRIMARY KEY,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_id TEXT,
    user_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    prediction INT,
    click_probability DOUBLE PRECISION,
    model_version TEXT NOT NULL,
    latency_ms DOUBLE PRECISION,
    status TEXT NOT NULL,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_inference_events_event_time
    ON inference_events (event_time DESC);

CREATE INDEX IF NOT EXISTS idx_inference_events_model_version
    ON inference_events (model_version);

CREATE INDEX IF NOT EXISTS idx_inference_events_status
    ON inference_events (status);
"""


def get_conn():
    return psycopg.connect(**DB_CONFIG)


def ensure_inference_events_table():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()


def insert_inference_event(payload: dict):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO inference_events (
                    request_id,
                    user_id,
                    item_id,
                    prediction,
                    click_probability,
                    model_version,
                    latency_ms,
                    status,
                    error_message
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    payload.get("request_id"),
                    payload["user_id"],
                    payload["item_id"],
                    payload.get("prediction"),
                    payload.get("click_probability"),
                    payload["model_version"],
                    payload.get("latency_ms"),
                    payload["status"],
                    payload.get("error_message"),
                ),
            )
        conn.commit()
