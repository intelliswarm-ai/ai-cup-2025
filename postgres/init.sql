-- Initialize database schema
-- This script is run once when the PostgreSQL container is first created

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables (these will also be created by SQLAlchemy, but we set up the schema here for clarity)
-- The actual tables are managed by SQLAlchemy ORM in the backend

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE mailbox_db TO mailbox_user;

-- Create indexes for better performance
-- Note: Tables will be created by SQLAlchemy models, but we can add custom configurations here if needed

-- Add any custom functions or triggers
CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully';
END $$;
