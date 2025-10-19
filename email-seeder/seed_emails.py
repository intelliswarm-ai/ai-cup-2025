#!/usr/bin/env python3
"""
Email Seeder Script
Generates and sends test emails to MailPit SMTP server
80% legitimate banking emails, 20% phishing emails
"""

import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

from email_templates import generate_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
SMTP_HOST = os.getenv("MAILPIT_SMTP_HOST", "mailpit")
SMTP_PORT = int(os.getenv("MAILPIT_SMTP_PORT", "1025"))
NUM_EMAILS = int(os.getenv("NUM_EMAILS", "2000"))
BATCH_SIZE = 50  # Send emails in batches
BATCH_DELAY = 2  # Seconds between batches

def send_email(smtp_server, email_data):
    """Send a single email via SMTP"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = email_data['subject']
        msg['From'] = email_data['sender']
        msg['To'] = f"customer{datetime.now().timestamp()}@bank.com"
        msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

        # Add body
        body = MIMEText(email_data['body'], 'plain')
        msg.attach(body)

        # Send email
        smtp_server.send_message(msg)

        return True

    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

def main():
    """Main seeding function"""
    logger.info(f"Starting email seeder...")
    logger.info(f"Target: {NUM_EMAILS} emails (80% legitimate, 20% phishing)")
    logger.info(f"MailPit SMTP: {SMTP_HOST}:{SMTP_PORT}")

    # Wait for MailPit to be ready
    logger.info("Waiting 10 seconds for MailPit to be ready...")
    time.sleep(10)

    sent_count = 0
    legitimate_count = 0
    phishing_count = 0
    failed_count = 0

    try:
        # Connect to SMTP server
        logger.info(f"Connecting to SMTP server at {SMTP_HOST}:{SMTP_PORT}")
        smtp_server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        smtp_server.set_debuglevel(0)  # Set to 1 for verbose SMTP debugging

        logger.info("Connected successfully! Starting to send emails...")

        # Send emails in batches
        for batch_num in range(0, NUM_EMAILS, BATCH_SIZE):
            batch_end = min(batch_num + BATCH_SIZE, NUM_EMAILS)
            logger.info(f"Sending batch {batch_num//BATCH_SIZE + 1}: emails {batch_num+1}-{batch_end}")

            for i in range(batch_num, batch_end):
                # Generate email
                email_data = generate_email()

                # Send email
                if send_email(smtp_server, email_data):
                    sent_count += 1
                    if email_data['is_phishing']:
                        phishing_count += 1
                    else:
                        legitimate_count += 1

                    if (i + 1) % 100 == 0:
                        logger.info(f"Progress: {i + 1}/{NUM_EMAILS} emails sent")
                else:
                    failed_count += 1

            # Delay between batches
            if batch_end < NUM_EMAILS:
                time.sleep(BATCH_DELAY)

        smtp_server.quit()

        # Final statistics
        logger.info("=" * 60)
        logger.info("EMAIL SEEDING COMPLETED!")
        logger.info("=" * 60)
        logger.info(f"Total emails sent: {sent_count}")
        logger.info(f"Legitimate emails: {legitimate_count} ({legitimate_count/sent_count*100:.1f}%)")
        logger.info(f"Phishing emails: {phishing_count} ({phishing_count/sent_count*100:.1f}%)")
        logger.info(f"Failed: {failed_count}")
        logger.info("=" * 60)
        logger.info(f"MailPit web interface: http://localhost:8025")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error during email seeding: {e}")
        raise

if __name__ == "__main__":
    main()
