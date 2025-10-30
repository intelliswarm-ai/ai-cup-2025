#!/usr/bin/env python3
"""
Database Migration Script: Add Team Assignment Fields
Run this script to add the new team assignment columns to the emails table
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the database migration to add team assignment fields"""

    migration_sql = """
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
    """

    try:
        logger.info("Starting database migration: Adding team assignment fields")

        with engine.connect() as conn:
            # Execute the migration
            conn.execute(text(migration_sql))
            conn.commit()

        logger.info("Migration completed successfully!")
        logger.info("The following columns have been added to the emails table:")
        logger.info("  - suggested_team: LLM-suggested team for email routing")
        logger.info("  - assigned_team: Team manually assigned by operator")
        logger.info("  - agentic_task_id: Task ID from agentic workflow")
        logger.info("  - team_assigned_at: Timestamp when team was assigned")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
