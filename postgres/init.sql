-- Initialize database schema
-- This script is run once when the PostgreSQL container is first created
-- NOTE: This only runs when the volume is empty (fresh installation)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- NOTE: Tables are managed by Liquibase migrations in backend/db/changelog/
-- This init.sql only sets up extensions, permissions, and helper functions

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
