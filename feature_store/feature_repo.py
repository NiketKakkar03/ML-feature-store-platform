from datetime import timedelta
from feast import Entity, FeatureView, Field
from feast.types import Float32, Int64
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import PostgreSQLSource

user = Entity(name="user_id", join_keys=["user_id"])
item = Entity(name="item_id", join_keys=["item_id"])

user_features_source = PostgreSQLSource(
    name="user_features_source",
    query="SELECT user_id, views_7d, clicks_7d, ctr_7d, views_1h, updated_at FROM user_features",
    timestamp_field="updated_at",
)

item_features_source = PostgreSQLSource(
    name="item_features_source",
    query="SELECT item_id, views_7d, clicks_7d, ctr_7d, updated_at FROM item_features",
    timestamp_field="updated_at",
)

user_features_fv = FeatureView(
    name="user_features",
    entities=[user],
    ttl=timedelta(days=7),
    schema=[
        Field(name="views_7d", dtype=Int64),
        Field(name="clicks_7d", dtype=Int64),
        Field(name="ctr_7d", dtype=Float32),
        Field(name="views_1h", dtype=Int64),
    ],
    source=user_features_source,
    online=True,
)

item_features_fv = FeatureView(
    name="item_features",
    entities=[item],
    ttl=timedelta(days=7),
    schema=[
        Field(name="views_7d", dtype=Int64),
        Field(name="clicks_7d", dtype=Int64),
        Field(name="ctr_7d", dtype=Float32),
    ],
    source=item_features_source,
    online=True,
)
