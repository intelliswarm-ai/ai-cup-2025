#!/usr/bin/env python3
"""
Fix malformed call_to_actions data in the database.
Converts dict format like {"task": "..."} to string format.
"""
import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mailbox:securemailbox@postgres:5432/mailbox_db")

def fix_cta_data():
    """Fix all malformed call_to_actions in the database"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get all emails with call_to_actions
        result = session.execute(text("""
            SELECT id, call_to_actions::text
            FROM emails
            WHERE call_to_actions IS NOT NULL
        """))

        emails = result.fetchall()
        print(f"Found {len(emails)} emails with call_to_actions")

        fixed_count = 0
        for email_id, ctas_json in emails:
            try:
                ctas = json.loads(ctas_json) if isinstance(ctas_json, str) else ctas_json

                if not isinstance(ctas, list):
                    continue

                # Check if any item is a dict
                needs_fix = False
                fixed_ctas = []

                for item in ctas:
                    if isinstance(item, dict):
                        # Extract string from dict using common keys
                        value = item.get("action") or item.get("task") or item.get("cta") or item.get("description") or item.get("text")
                        if value and isinstance(value, str):
                            fixed_ctas.append(value)
                            needs_fix = True
                        else:
                            # Skip items without extractable strings
                            needs_fix = True
                    elif isinstance(item, str):
                        fixed_ctas.append(item)

                if needs_fix:
                    # Update the database
                    session.execute(
                        text("UPDATE emails SET call_to_actions = :ctas WHERE id = :id"),
                        {"ctas": json.dumps(fixed_ctas), "id": email_id}
                    )
                    fixed_count += 1
                    print(f"Fixed email {email_id}: {len(ctas)} items -> {len(fixed_ctas)} items")

            except Exception as e:
                print(f"Error processing email {email_id}: {e}")
                continue

        session.commit()
        print(f"\nFixed {fixed_count} emails")

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fix_cta_data()
