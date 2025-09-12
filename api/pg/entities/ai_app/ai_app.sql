-- Main table for AI Apps
CREATE TABLE ai_app (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    system_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL,
    modified_at TIMESTAMPTZ NOT NULL
);

-- Child table for the tabs array
CREATE TABLE ai_app_tab (
    id SERIAL PRIMARY KEY,
    ai_app_id INTEGER NOT NULL REFERENCES ai_app(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    system_name TEXT NOT NULL,
    tab_type TEXT NOT NULL,
    config JSONB NOT NULL,  -- stores { "agent": ..., } or { "rag_tool": ... }
    UNIQUE (ai_app_id, system_name)
);

-- Index on config if you need to query into JSONB
CREATE INDEX idx_ai_app_tab_config ON ai_app_tab USING GIN (config);
