-- Top-level evaluations table, mirrors main document
CREATE TABLE evaluations (
    id TEXT PRIMARY KEY,                   -- MongoDB _id.$oid
    job_id TEXT NOT NULL,
    type TEXT NOT NULL,
    tool JSONB NOT NULL,                   -- entire tool object
    variant_name TEXT NOT NULL,            -- tool.variant_name
    variant_object JSONB NOT NULL,         -- detailed variant settings
    response_format JSONB,                 -- response_format object
    test_sets TEXT[] NOT NULL,             -- list of test sets
    started_at TIMESTAMPTZ NOT NULL,       -- when job started
    status TEXT NOT NULL,
    errors TEXT[] DEFAULT '{}',            -- any errors
    finished_at TIMESTAMPTZ NOT NULL       -- when job finished
);

-- Child table for each result within evaluations.results
CREATE TABLE evaluation_results (
    id UUID PRIMARY KEY,                   -- result.id
    evaluation_id TEXT NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    model_version TEXT NOT NULL,
    usage JSONB NOT NULL,                  -- usage.completion_tokens, prompt_tokens
    latency DOUBLE PRECISION,              -- in ms
    generated_output JSONB,                -- the agent’s JSON output
    test_set TEXT,                         -- which test set this result belongs to
    evaluated_at TIMESTAMPTZ,              -- timestamp of evaluation
    expected_output JSONB,                 -- any expected output
    user_message TEXT,                     -- original user message
    iteration INT,                         -- iteration number
    score INT                              -- optional score
);
