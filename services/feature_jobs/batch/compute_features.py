import pandas as pd
from datetime import datetime, timedelta
from db import get_connection, create_feature_tables

def load_events(conn):
    query = """
        SELECT user_id, item_id, event_type, ts
        FROM events
        WHERE ts >= NOW() - INTERVAL '7 days'
    """
    df = pd.read_sql(query, conn)
    print(f"Loaded {len(df)} events from last 7 days")
    return df

def compute_user_features(df):
    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"]).dt.tz_localize(None)

    now = pd.Timestamp.utcnow().tz_localize(None)
    one_hour_ago = now - pd.Timedelta(hours=1)

    views_7d = (
        df[df["event_type"] == "view"]
        .groupby("user_id")
        .size()
        .rename("views_7d")
    )
    clicks_7d = (
        df[df["event_type"] == "click"]
        .groupby("user_id")
        .size()
        .rename("clicks_7d")
    )

    df_1h = df[df["ts"] >= one_hour_ago]
    views_1h = (
        df_1h[df_1h["event_type"] == "view"]
        .groupby("user_id")
        .size()
        .rename("views_1h")
    )

    user_features = pd.concat([views_7d, clicks_7d, views_1h], axis=1).fillna(0)
    user_features[["views_7d", "clicks_7d", "views_1h"]] = user_features[
        ["views_7d", "clicks_7d", "views_1h"]
    ].astype(int)

    user_features["ctr_7d"] = (
        user_features["clicks_7d"]
        / (user_features["views_7d"] + user_features["clicks_7d"])
    ).fillna(0).round(4)

    return user_features.reset_index()


def compute_item_features(df):
    views_7d  = df[df["event_type"] == "view"].groupby("item_id").size().rename("views_7d")
    clicks_7d = df[df["event_type"] == "click"].groupby("item_id").size().rename("clicks_7d")

    item_features = pd.concat([views_7d, clicks_7d], axis=1).fillna(0).astype(int)
    item_features["ctr_7d"] = (
        item_features["clicks_7d"] / (item_features["views_7d"] + item_features["clicks_7d"])
    ).fillna(0).round(4)
    item_features = item_features.reset_index()

    print(f"Computed features for {len(item_features)} items")
    return item_features

def write_user_features(conn, df):
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO user_features (user_id, views_7d, clicks_7d, ctr_7d, views_1h, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                views_7d   = EXCLUDED.views_7d,
                clicks_7d  = EXCLUDED.clicks_7d,
                ctr_7d     = EXCLUDED.ctr_7d,
                views_1h   = EXCLUDED.views_1h,
                updated_at = NOW()
        """, (int(row.user_id), int(row.views_7d), int(row.clicks_7d),
              float(row.ctr_7d), int(row.views_1h)))
    conn.commit()
    cursor.close()
    print(f"Wrote {len(df)} user feature rows to Postgres")

def write_item_features(conn, df):
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO item_features (item_id, views_7d, clicks_7d, ctr_7d, updated_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (item_id) DO UPDATE SET
                views_7d   = EXCLUDED.views_7d,
                clicks_7d  = EXCLUDED.clicks_7d,
                ctr_7d     = EXCLUDED.ctr_7d,
                updated_at = NOW()
        """, (int(row.item_id), int(row.views_7d), int(row.clicks_7d), float(row.ctr_7d)))
    conn.commit()
    cursor.close()
    print(f"Wrote {len(df)} item feature rows to Postgres")

def run():
    print("Starting batch feature computation...")
    create_feature_tables()

    conn = get_connection()
    df = load_events(conn)

    if df.empty:
        print("No events found. Generate some first!")
        return

    user_features = compute_user_features(df)
    item_features = compute_item_features(df)

    write_user_features(conn, user_features)
    write_item_features(conn, item_features)

    conn.close()
    print("Batch feature job complete!")

    # Preview results
    conn2 = get_connection()
    cursor = conn2.cursor()
    cursor.execute("SELECT * FROM user_features LIMIT 5;")
    rows = cursor.fetchall()
    print("\nSample user_features:")
    print(f"{'user_id':>8} {'views_7d':>10} {'clicks_7d':>10} {'ctr_7d':>8} {'views_1h':>10}")
    for row in rows:
        print(f"{row[0]:>8} {row[1]:>10} {row[2]:>10} {row[3]:>8.4f} {row[4]:>10}")
    cursor.close()
    conn2.close()

if __name__ == "__main__":
    run()
