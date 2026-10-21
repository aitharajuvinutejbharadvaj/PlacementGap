CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS run_checkpoints (thread_id text PRIMARY KEY, state jsonb NOT NULL, updated_at timestamptz DEFAULT now());
CREATE TABLE IF NOT EXISTS student_profiles (student_id text PRIMARY KEY, profile jsonb NOT NULL, updated_at timestamptz DEFAULT now());
CREATE TABLE IF NOT EXISTS semantic_cache (content_hash text PRIMARY KEY, role text, result jsonb NOT NULL, expires_at timestamptz NOT NULL);
