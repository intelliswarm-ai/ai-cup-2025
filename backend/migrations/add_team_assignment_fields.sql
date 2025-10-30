-- Migration: Add team assignment fields to emails table
-- Date: 2025-10-30
-- Description: Adds fields for LLM-suggested team assignment and agentic workflow tracking

-- Add suggested_team column
ALTER TABLE emails
ADD COLUMN IF NOT EXISTS suggested_team VARCHAR;

-- Add assigned_team column
ALTER TABLE emails
ADD COLUMN IF NOT EXISTS assigned_team VARCHAR;

-- Add agentic_task_id column
ALTER TABLE emails
ADD COLUMN IF NOT EXISTS agentic_task_id VARCHAR;

-- Add team_assigned_at column
ALTER TABLE emails
ADD COLUMN IF NOT EXISTS team_assigned_at TIMESTAMP;

-- Add comments for documentation
COMMENT ON COLUMN emails.suggested_team IS 'LLM-suggested team for email routing';
COMMENT ON COLUMN emails.assigned_team IS 'Team manually assigned by operator';
COMMENT ON COLUMN emails.agentic_task_id IS 'Task ID from agentic workflow for tracking';
COMMENT ON COLUMN emails.team_assigned_at IS 'Timestamp when team was assigned by operator';
