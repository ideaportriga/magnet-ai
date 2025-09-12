-- Table to store evaluation set metadata
CREATE TABLE evaluation_sets (
    id TEXT PRIMARY KEY,                       -- MongoDB ObjectId
    system_name VARCHAR(255) NOT NULL,         -- system identifier
    name VARCHAR(255) NOT NULL,                -- human-readable name
    description TEXT,                          -- free-form description
    type VARCHAR(100) NOT NULL,                -- e.g. 'rag_tool'
    created_at TIMESTAMPTZ NOT NULL,           -- from _metadata.created_at
    modified_at TIMESTAMPTZ NOT NULL           -- from _metadata.modified_at
);

-- Table to store each item in the evaluation set
CREATE TABLE evaluation_set_items (
    id SERIAL PRIMARY KEY,
    evaluation_set_id TEXT NOT NULL REFERENCES evaluation_sets(id) ON DELETE CASCADE,
    user_input TEXT NOT NULL,                  -- input from the user
    expected_result TEXT NOT NULL              -- expected response
);

-- Optional index for faster lookups by evaluation_set_id
CREATE INDEX ON evaluation_set_items(evaluation_set_id);
