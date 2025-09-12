-- Initialize database with pgvector extension
-- This script will be automatically executed when the container starts

-- Create the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify the extension is installed
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE magnet_dev TO postgres;

-- Create a test table to verify vector functionality
CREATE TABLE IF NOT EXISTS test_vectors (
    id SERIAL PRIMARY KEY,
    embedding vector(3),
    metadata JSONB
);

-- Insert a test vector
INSERT INTO test_vectors (embedding, metadata) 
VALUES ('[0.1,0.2,0.3]'::vector(3), '{"test": true}');

-- Create an index for vector similarity search
CREATE INDEX IF NOT EXISTS test_vectors_embedding_idx 
ON test_vectors USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Create a table for OpenAI embeddings (1536 dimensions)
CREATE TABLE IF NOT EXISTS embeddings_openai (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create an index for the OpenAI embeddings
CREATE INDEX IF NOT EXISTS embeddings_openai_embedding_idx 
ON embeddings_openai USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

COMMENT ON TABLE test_vectors IS 'Test table for vector operations';
COMMENT ON TABLE embeddings_openai IS 'Table for storing OpenAI embeddings (1536 dimensions)';
