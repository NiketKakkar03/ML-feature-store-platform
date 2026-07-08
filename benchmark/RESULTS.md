# Serving latency benchmark

Measured **2026-07-08** on a local Docker Compose run (Windows host, Docker
Desktop, 16 vCPU / ~7 GB allotted to the Linux engine). Latency is recorded
server-side per request in the `inference_events.latency_ms` column, covering
the full `/predict` path: model-version routing → Feast online feature fetch
from Redis → scikit-learn inference → Postgres logging.

## Method

1. Bring up the stack: `docker compose -f infra/docker-compose.yml up -d --build`
2. Generate 1000 synthetic events: `curl -X POST http://localhost:8000/generate-batch/1000`
3. Compute features: `docker compose -f infra/docker-compose.yml run --rm batch_features`
4. Materialize into Redis: `feast apply` then `feast materialize 2020-01-01T00:00:00 2030-01-01T00:00:00`
5. Fire 500 requests across 10 users × 20 items: `./benchmark/run_benchmark.sh 500`

## Results (500 requests)

| scope | n | avg | p50 | p95 | p99 | min | max |
|-------|---|-----|-----|-----|-----|-----|-----|
| overall | 500 | 6.79 ms | 6.60 ms | 8.11 ms | 9.87 ms | 5.81 ms | 15.18 ms |
| model v1 | 250 | 6.73 ms | 6.56 ms | 7.73 ms | — | — | — |
| model v2 | 250 | 6.86 ms | 6.65 ms | 8.28 ms | — | — | — |
| cold (first request) | 1 | 15.18 ms | — | — | — | — | — |
| warm (rest) | 499 | 6.78 ms | 6.60 ms | — | — | 5.81 ms | 14.19 ms |

## Findings

1. **Warm serving latency is single-digit milliseconds** end to end: p50 6.6 ms,
   p95 8.1 ms, p99 9.9 ms. The Redis online-store lookup itself is sub-millisecond;
   the rest of the budget is Feast overhead, inference, and Postgres logging.
2. **The two model versions have no meaningful latency difference** (v1 p50
   6.56 ms vs v2 p50 6.65 ms). The deterministic hash-based A/B split governs which
   model scores a request, not how fast it responds.
3. **Cold start costs more than steady state.** The first request after the store
   is idle was ~15 ms here; in earlier ad-hoc runs, the first request after a long
   idle gap spiked as high as ~400 ms before settling back to the ~6–13 ms band.
   The overhead is Feast/Redis connection warmup, not model choice.
