CREATE TABLE IF NOT EXISTS inference_events (
    id BIGSERIAL PRIMARY KEY,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_id TEXT,
    user_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    prediction INT,
    click_probability DOUBLE PRECISION,
    model_version TEXT NOT NULL,
    latency_ms DOUBLE PRECISION,
    status TEXT NOT NULL,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_inference_events_event_time
    ON inference_events (event_time DESC);

CREATE INDEX IF NOT EXISTS idx_inference_events_model_version
    ON inference_events (model_version);

CREATE INDEX IF NOT EXISTS idx_inference_events_status
    ON inference_events (status);
