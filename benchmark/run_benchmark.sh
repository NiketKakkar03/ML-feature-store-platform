#!/usr/bin/env bash
# Latency benchmark for the model serving path.
#
# Prerequisites: the full stack is up (docker compose -f infra/docker-compose.yml up -d --build),
# events have been generated, and features have been materialized into Redis:
#   curl -X POST http://localhost:8000/generate-batch/1000
#   docker compose -f infra/docker-compose.yml run --rm batch_features
#   docker exec model_service sh -c "cd /app/feature_store && feast apply"
#   docker exec model_service sh -c "cd /app/feature_store && feast materialize 2020-01-01T00:00:00 2030-01-01T00:00:00"
#
# Usage: ./benchmark/run_benchmark.sh [N_REQUESTS]   (default 500)

set -euo pipefail
N="${1:-500}"
PREDICT_URL="http://localhost:8001/predict"

PSQL() { docker exec postgres psql -U postgres -d featurestore "$@"; }

PREV_MAX=$(PSQL -tAc "SELECT COALESCE(max(id),0) FROM inference_events;")
echo "Firing $N requests (baseline inference_events id = $PREV_MAX)..."

start=$(date +%s)
for i in $(seq 1 "$N"); do
  u=$(( (i % 10) + 1 ))
  it=$(( (i % 20) + 1 ))
  curl -s -o /dev/null -X POST "$PREDICT_URL" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":$u,\"item_id\":$it}"
done
echo "Done in $(( $(date +%s) - start ))s."

echo ""; echo "== Overall =="
PSQL -c "
SELECT count(*) AS n,
  round(avg(latency_ms)::numeric,2)                                        AS avg_ms,
  round(percentile_cont(0.5)  WITHIN GROUP (ORDER BY latency_ms)::numeric,2) AS p50,
  round(percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms)::numeric,2) AS p95,
  round(percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms)::numeric,2) AS p99,
  round(min(latency_ms)::numeric,2) AS min, round(max(latency_ms)::numeric,2) AS max
FROM inference_events WHERE id > $PREV_MAX;"

echo "== Per model version =="
PSQL -c "
SELECT model_version, count(*) AS n,
  round(avg(latency_ms)::numeric,2)                                         AS avg_ms,
  round(percentile_cont(0.5)  WITHIN GROUP (ORDER BY latency_ms)::numeric,2) AS p50,
  round(percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms)::numeric,2) AS p95
FROM inference_events WHERE id > $PREV_MAX GROUP BY model_version ORDER BY model_version;"

echo "== Cold (first request) vs warm (rest) =="
PSQL -c "
WITH o AS (SELECT latency_ms, row_number() OVER (ORDER BY id) AS seq
           FROM inference_events WHERE id > $PREV_MAX)
SELECT CASE WHEN seq=1 THEN 'cold_first' ELSE 'warm_rest' END AS bucket,
  count(*) AS n,
  round(avg(latency_ms)::numeric,2)                                         AS avg_ms,
  round(percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms)::numeric,2)  AS p50,
  round(min(latency_ms)::numeric,2) AS min, round(max(latency_ms)::numeric,2) AS max
FROM o GROUP BY 1 ORDER BY 1;"
