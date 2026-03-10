import pandas as pd
import psycopg2
from feast import FeatureStore

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5433,
        dbname="featurestore",
        user="postgres",
        password="postgres"
    )

def load_entity_df():
    conn = get_connection()
    query = """
        SELECT
            user_id,
            item_id,
            ts AS event_timestamp,
            CASE WHEN event_type = 'click' THEN 1 ELSE 0 END AS label
        FROM events
        WHERE event_type IN ('view', 'click')
        ORDER BY ts
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def main():
    entity_df = load_entity_df()
    store = FeatureStore(repo_path="../../feature_store")

    training_df = store.get_historical_features(
        entity_df=entity_df,
        full_feature_names=True,
        features=[
            "user_features:views_7d",
            "user_features:clicks_7d",
            "user_features:ctr_7d",
            "user_features:views_1h",
            "item_features:views_7d",
            "item_features:clicks_7d",
            "item_features:ctr_7d",
        ],
    ).to_df()

    training_df = training_df.dropna()
    training_df.to_csv("training_dataset.csv", index=False)
    print(training_df.head())
    print(f"Saved training dataset with {len(training_df)} rows")

if __name__ == "__main__":
    main()
