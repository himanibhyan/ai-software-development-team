-- Database initialization script for AI Software Development Team

-- Create custom enum types
DO $$ BEGIN
    CREATE TYPE project_status AS ENUM (
        'pending', 'running', 'completed', 'failed', 'refining'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE agent_status AS ENUM (
        'pending', 'running', 'completed', 'failed', 'skipped'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create extension for full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
