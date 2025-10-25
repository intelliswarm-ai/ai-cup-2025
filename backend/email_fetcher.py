"""
Background email fetcher service
Fetches emails from MailPit in batches of 100 with 10 second delays
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from mailpit_client import MailPitClient
from database import SessionLocal
from models import Email
from events import broadcaster

logger = logging.getLogger(__name__)


class EmailFetcherService:
    """Background service to fetch emails from MailPit in scheduled batches"""

    def __init__(self):
        self.mailpit_client = MailPitClient()
        self.is_running = False
        self.fetch_task: Optional[asyncio.Task] = None

    async def start_fetching(self):
        """Start the scheduled email fetching process"""
        if self.is_running:
            logger.info("Email fetcher is already running")
            return

        self.is_running = True
        logger.info("Starting scheduled email fetcher...")

        # Broadcast start event
        await broadcaster.broadcast("fetch_started", {
            "message": "Email fetching started",
            "batch_size": 100,
            "delay_seconds": 10
        })

        try:
            total_fetched = 0
            batch_number = 0
            start_offset = 0

            while self.is_running:
                batch_number += 1
                logger.info(f"Fetching batch {batch_number} (100 emails from offset {start_offset})...")

                # Get database session
                db = SessionLocal()

                try:
                    # Fetch batch of 100 emails from MailPit with pagination
                    messages_data = await self.mailpit_client.get_messages(limit=100, start=start_offset)
                    messages = messages_data.get("messages", [])
                    total_in_mailpit = messages_data.get("total", 0)

                    fetched_count = 0
                    for msg in messages:
                        msg_id = msg.get("ID")

                        # Check if email already exists
                        existing = db.query(Email).filter(Email.mailpit_id == msg_id).first()
                        if existing:
                            continue

                        # Fetch full message details
                        full_msg = await self.mailpit_client.get_message(msg_id)

                        # Fetch headers separately to get custom headers
                        headers = await self.mailpit_client.get_message_headers(msg_id)

                        # Extract ground truth labels from custom headers
                        label = None
                        phishing_type = None

                        if "X-Email-Label" in headers:
                            label = int(headers["X-Email-Label"][0])

                        if "X-Email-Phishing-Type" in headers:
                            phishing_type = headers["X-Email-Phishing-Type"][0]

                        # Create email record
                        # Use 'Created' from msg (list API) or 'Date' from full_msg
                        created_str = msg.get("Created") or full_msg.get("Date", "")
                        received_at = datetime.fromisoformat(created_str.replace("Z", "+00:00")) if created_str else datetime.utcnow()

                        email = Email(
                            mailpit_id=msg_id,
                            subject=full_msg.get("Subject", ""),
                            sender=full_msg.get("From", {}).get("Address", ""),
                            recipient=full_msg.get("To", [{}])[0].get("Address", "") if full_msg.get("To") else "",
                            body_text=full_msg.get("Text", ""),
                            body_html=full_msg.get("HTML", ""),
                            received_at=received_at,
                            label=label,
                            phishing_type=phishing_type
                        )

                        db.add(email)
                        fetched_count += 1

                    db.commit()
                    total_fetched += fetched_count

                    logger.info(f"Batch {batch_number}: Fetched {fetched_count} emails (Total: {total_fetched})")

                    # Broadcast fetch progress
                    await broadcaster.broadcast("emails_fetched", {
                        "batch": batch_number,
                        "fetched_in_batch": fetched_count,
                        "total_fetched": total_fetched,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                    # Move to next batch
                    start_offset += len(messages)

                    # If no more messages available or no new emails fetched, stop
                    if len(messages) == 0 or start_offset >= total_in_mailpit:
                        logger.info(f"All emails fetched from MailPit (Total: {total_fetched}, MailPit total: {total_in_mailpit})")
                        await broadcaster.broadcast("fetch_completed", {
                            "message": "All emails fetched",
                            "total_fetched": total_fetched,
                            "batches": batch_number
                        })
                        self.is_running = False
                        break

                    # Wait 10 seconds before next batch
                    if self.is_running:
                        logger.info("Waiting 10 seconds before next batch...")
                        await asyncio.sleep(10)

                except Exception as e:
                    logger.error(f"Error fetching batch {batch_number}: {e}")
                    await broadcaster.broadcast("fetch_error", {
                        "message": str(e),
                        "batch": batch_number
                    })
                    # Continue to next batch after error
                    await asyncio.sleep(10)

                finally:
                    db.close()

        except asyncio.CancelledError:
            logger.info("Email fetcher task cancelled")
            self.is_running = False
        except Exception as e:
            logger.error(f"Fatal error in email fetcher: {e}")
            await broadcaster.broadcast("fetch_error", {
                "message": f"Fatal error: {str(e)}"
            })
            self.is_running = False

    async def stop_fetching(self):
        """Stop the scheduled email fetching process"""
        if not self.is_running:
            logger.info("Email fetcher is not running")
            return

        logger.info("Stopping email fetcher...")
        self.is_running = False

        if self.fetch_task and not self.fetch_task.done():
            self.fetch_task.cancel()
            try:
                await self.fetch_task
            except asyncio.CancelledError:
                pass

        await broadcaster.broadcast("fetch_stopped", {
            "message": "Email fetching stopped"
        })

    def get_status(self):
        """Get the current status of the fetcher"""
        return {
            "is_running": self.is_running,
            "batch_size": 100,
            "delay_seconds": 10
        }


# Global fetcher instance
email_fetcher = EmailFetcherService()
