import sys
from pathlib import Path
from services.model_service.routing import choose_model_version

ROOT = Path(__file__).resolve().parents[2]
MODEL_SERVICE_DIR = ROOT / "services" / "model_service"
sys.path.append(str(MODEL_SERVICE_DIR))


def test_same_user_gets_same_variant():
    user_id = 123
    first = choose_model_version(user_id, rollout_percent=20)
    second = choose_model_version(user_id, rollout_percent=20)
    assert first == second


def test_variant_is_valid():
    for user_id in range(1, 101):
        variant = choose_model_version(user_id, rollout_percent=20)
        assert variant in {"v1", "v2"}


def test_zero_percent_routes_all_to_v1():
    for user_id in range(1, 51):
        assert choose_model_version(user_id, rollout_percent=0) == "v1"


def test_hundred_percent_routes_all_to_v2():
    for user_id in range(1, 51):
        assert choose_model_version(user_id, rollout_percent=100) == "v2"


def test_split_produces_both_variants():
    variants = {choose_model_version(user_id, rollout_percent=20) for user_id in range(1, 500)}
    assert variants == {"v1", "v2"}
