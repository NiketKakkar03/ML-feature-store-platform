from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from feast import FeatureStore
from prometheus_fastapi_instrumentator import Instrumentator
import joblib
import numpy as np
import os
import time
import logging

from routing import choose_model_version
from db import ensure_inference_events_table, insert_inference_event
from middleware import RequestLoggingMiddleware


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("model_service")


app = FastAPI(title="Model Service")
app.add_middleware(RequestLoggingMiddleware)
instrumentator = Instrumentator().instrument(app)


FEATURE_REPO = os.getenv("FEATURE_REPO", "/app/feature_store")
ROLLOUT_PERCENT = int(os.getenv("ROLLOUT_PERCENT", "20"))
SMOKE_TEST_MODE = os.getenv("SMOKE_TEST_MODE", "false").lower() == "true"


if not SMOKE_TEST_MODE:
    store = FeatureStore(repo_path=FEATURE_REPO)
    MODELS = {
        "v1": joblib.load("/app/services/model_training/models/model.joblib"),
        "v2": joblib.load("/app/services/model_training/models/model_2.joblib"),
    }
else:
    store = None
    MODELS = {}


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


@app.on_event("startup")
def startup_event():
    instrumentator.expose(app)

    if not SMOKE_TEST_MODE:
        ensure_inference_events_table()

    logger.info(
        {
            "event": "startup_complete",
            "smoke_test_mode": SMOKE_TEST_MODE,
            "available_models": list(MODELS.keys()),
            "rollout_percent_v2": ROLLOUT_PERCENT,
        }
    )


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "smoke_test_mode": SMOKE_TEST_MODE,
        "available_model_versions": list(MODELS.keys()),
        "rollout_percent_v2": ROLLOUT_PERCENT,
    }


def safe_insert_event(payload: dict) -> None:
    if SMOKE_TEST_MODE:
        return

    try:
        insert_inference_event(payload)
    except Exception:
        logger.exception({"event": "inference_event_insert_failed", "payload": payload})


@app.post("/predict")
def predict(req: PredictionRequest, request: Request):
    if SMOKE_TEST_MODE:
        raise HTTPException(status_code=503, detail="Predict disabled in smoke test mode")

    request_id = getattr(request.state, "request_id", None)
    start = time.perf_counter()
    model_version = choose_model_version(req.user_id)
    model = MODELS[model_version]

    try:
        online = store.get_online_features(
            features=FEATURE_REFS,
            entity_rows=[{"user_id": req.user_id, "item_id": req.item_id}],
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
            latency_ms = round((time.perf_counter() - start) * 1000, 2)

            safe_insert_event(
                {
                    "request_id": request_id,
                    "user_id": req.user_id,
                    "item_id": req.item_id,
                    "prediction": None,
                    "click_probability": None,
                    "model_version": model_version,
                    "latency_ms": latency_ms,
                    "status": "missing_features",
                    "error_message": "Missing online features for entity",
                }
            )

            raise HTTPException(status_code=404, detail="Missing online features for entity")

        X = np.array([[values[c] for c in MODEL_COLUMNS]], dtype=float)
        score = float(model.predict_proba(X)[0][1])
        pred = int(model.predict(X)[0])
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        safe_insert_event(
            {
                "request_id": request_id,
                "user_id": req.user_id,
                "item_id": req.item_id,
                "prediction": pred,
                "click_probability": score,
                "model_version": model_version,
                "latency_ms": latency_ms,
                "status": "success",
                "error_message": None,
            }
        )

        return {
            "request_id": request_id,
            "user_id": req.user_id,
            "item_id": req.item_id,
            "prediction": pred,
            "click_probability": score,
            "model_version": model_version,
            "features_used": values,
        }

    except HTTPException:
        raise

    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        safe_insert_event(
            {
                "request_id": request_id,
                "user_id": req.user_id,
                "item_id": req.item_id,
                "prediction": None,
                "click_probability": None,
                "model_version": model_version,
                "latency_ms": latency_ms,
                "status": "error",
                "error_message": str(e),
            }
        )

        logger.exception(
            {
                "event": "prediction_failed",
                "request_id": request_id,
                "user_id": req.user_id,
                "item_id": req.item_id,
                "model_version": model_version,
                "error": str(e),
            }
        )

        raise HTTPException(status_code=500, detail="Internal server error")
