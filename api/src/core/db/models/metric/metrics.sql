-- Table to store metrics from MongoDB
CREATE TABLE metrics (
    -- MongoDB document ID
    id          TEXT PRIMARY KEY,
    feature_name        TEXT NOT NULL,
    feature_system_name TEXT NOT NULL,
    feature_type        TEXT,
    feature_id          TEXT,
    feature_variant     TEXT,
    channel             TEXT,
    source              TEXT,
    status              TEXT,
    start_time          TIMESTAMPTZ,
    end_time            TIMESTAMPTZ,
    latency             DOUBLE PRECISION,
    cost                NUMERIC,
    trace_id            TEXT,
    user_id             TEXT,
    consumer_name       TEXT,
    consumer_type       TEXT,
    -- nested extra_data (question/answer) as JSON
    extra_data          JSONB,
    -- nested x_attributes (e.g., org-id) as JSON
    x_attributes        JSONB
);

-- Index on start_time for time-based queries
CREATE INDEX idx_metrics_start_time ON metrics(start_time);

-- Foreign-key example: if you have a separate features table for feature_id:
-- ALTER TABLE metrics
--   ADD CONSTRAINT fk_feature
--   FOREIGN KEY (feature_id)
--   REFERENCES features(id);
