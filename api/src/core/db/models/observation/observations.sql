-- Stores each observation document from MongoDB
CREATE TABLE observations (
    id               TEXT           PRIMARY KEY,         -- MongoDB _id.$oid
    name             TEXT           NOT NULL,            -- name of the request
    type             TEXT           NOT NULL,            -- type of the operation
    start_time       TIMESTAMPTZ    NOT NULL,            -- start timestamp
    end_time         TIMESTAMPTZ    NOT NULL,            -- end timestamp
    latency          DOUBLE PRECISION NOT NULL,          -- duration in ms
    status           TEXT           NOT NULL,            -- success/failure
    status_message   TEXT,                              -- optional error/message
    metadata         JSONB          NOT NULL DEFAULT '{}'-- additional metadata
    , description    TEXT                               -- optional description
    , model          JSONB          NOT NULL             -- full model object
    , input          JSONB          NOT NULL             -- array of input messages
    , output         JSONB          NOT NULL             -- assistant output JSON
    , usage_details  JSONB          NOT NULL             -- usage metrics
    , cost_details   JSONB          NOT NULL             -- cost breakdown
    , prompt_template JSONB         NOT NULL             -- prompt template info
);

-- Comments on key columns
COMMENT ON TABLE observations IS 'Observation records migrated from MongoDB.';
COMMENT ON COLUMN observations.id IS 'Original MongoDB ObjectID as text.';
COMMENT ON COLUMN observations.model IS 'Model details including name, provider, parameters.';
COMMENT ON COLUMN observations.input IS 'Conversation history array.';
COMMENT ON COLUMN observations.usage_details IS 'Token usage statistics.';
