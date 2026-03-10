import hashlib
import os

ROLLOUT_PERCENT = int(os.getenv("ROLLOUT_PERCENT", "20"))

def choose_model_version(user_id: int, rollout_percent: int | None = None) -> str:
    percent = ROLLOUT_PERCENT if rollout_percent is None else rollout_percent
    bucket = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16) % 100
    return "v2" if bucket < percent else "v1"
