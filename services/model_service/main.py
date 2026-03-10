from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from feast import FeatureStore
import joblib
import numpy as np
from pathlib import Path

app = FastAPI(title="Model Service")

FEATURE_REPO = "/app/feature_store"
MODEL_PATH = "/app/services/model_training/models/model.joblib"

store = FeatureStore(repo_path=str(FEATURE_REPO))
model = joblib.load(MODEL_PATH)

FEATURE_REFS = [
    "user_features:views_7d",
    "user_features:clicks_7d",
    "user_features:ctr_7d",
    "user_features:views_1h",
    "item_features:views_7d",
    "item_features:clicks_7d",
    "item_features:ctr_7d",
]

MODEL_COLUMNS = [
    "user_features__views_7d",
    "user_features__clicks_7d",
    "user_features__ctr_7d",
    "user_features__views_1h",
    "item_features__views_7d",
    "item_features__clicks_7d",
    "item_features__ctr_7d",
]

class PredictionRequest(BaseModel):
    user_id: int
    item_id: int

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/predict")
def predict(req: PredictionRequest):
    online = store.get_online_features(
        features=FEATURE_REFS,
        entity_rows=[{"user": req.user_id, "item": req.item_id}], 
        full_feature_names=True,
    ).to_dict()

    values = {
        "user_features__views_7d": online.get("user_features__views_7d", [None])[0],
        "user_features__clicks_7d": online.get("user_features__clicks_7d", [None])[0],
        "user_features__ctr_7d": online.get("user_features__ctr_7d", [None])[0],
        "user_features__views_1h": online.get("user_features__views_1h", [None])[0],
        "item_features__views_7d": online.get("item_features__views_7d", [None])[0],
        "item_features__clicks_7d": online.get("item_features__clicks_7d", [None])[0],
        "item_features__ctr_7d": online.get("item_features__ctr_7d", [None])[0],
    }

    if any(values[c] is None for c in MODEL_COLUMNS):
        raise HTTPException(status_code=404, detail="Missing online features for entity")

    X = np.array([[values[c] for c in MODEL_COLUMNS]], dtype=float)
    score = float(model.predict_proba(X)[0][1])
    pred = int(model.predict(X)[0])

    return {
        "user_id": req.user_id,
        "item_id": req.item_id,
        "prediction": pred,
        "click_probability": score,
        "features_used": values,
    }
