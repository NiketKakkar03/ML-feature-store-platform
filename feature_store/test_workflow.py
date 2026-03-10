from feast import FeatureStore
import pandas as pd
from datetime import datetime

store = FeatureStore(repo_path=".")

entity_df = pd.DataFrame.from_dict({
    "user_id": [1, 2, 3],
    "event_timestamp": [
        datetime.utcnow(),
        datetime.utcnow(),
        datetime.utcnow(),
    ],
})

training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "user_features:views_7d",
        "user_features:clicks_7d",
        "user_features:ctr_7d",
        "user_features:views_1h",
    ],
).to_df()

print(training_df)

store.materialize_incremental(end_date=datetime.utcnow())

online_features = store.get_online_features(
    features=[
        "user_features:views_7d",
        "user_features:clicks_7d",
        "user_features:ctr_7d",
        "user_features:views_1h",
    ],
    entity_rows=[{"user_id": 1}, {"user_id": 2}],
).to_dict()

print(online_features)
