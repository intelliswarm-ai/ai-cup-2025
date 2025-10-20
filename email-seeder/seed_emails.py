#!/usr/bin/env python3
"""
Email Seeder Script
Loads emails from Kaggle dataset and sends to MailPit SMTP server
Dataset: Phishing and Legitimate Emails Dataset by Kuladeep19
https://www.kaggle.com/datasets/kuladeep19/phishing-and-legitimate-emails-dataset
"""

import os
import time
import smtplib
import csv
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
SMTP_HOST = os.getenv("MAILPIT_SMTP_HOST", "mailpit")
SMTP_PORT = int(os.getenv("MAILPIT_SMTP_PORT", "1025"))
DATASET_PATH = os.getenv("DATASET_PATH", "/dataset/phishing_legit_dataset_KD_10000.csv")
NUM_EMAILS = int(os.getenv("NUM_EMAILS", "5000"))  # How many from dataset to send
BATCH_SIZE = 50  # Send emails in batches
BATCH_DELAY = 2  # Seconds between batches

def parse_email_from_csv_row(row):
    """Parse email data from CSV row"""
    text = row['text']
    label = int(row['label'])  # 1 = phishing, 0 = legitimate
    phishing_type = row['phishing_type']

    # Extract subject from text (format: "Subject: <subject>\n\n<body>")
    subject_match = re.match(r'Subject:\s*(.+?)\n\n', text, re.DOTALL)
    if subject_match:
        subject = subject_match.group(1).strip()
        body = text[subject_match.end():].strip()
    else:
        # If no subject found, use first line as subject
        lines = text.split('\n', 1)
        subject = lines[0][:100]  # First 100 chars
        body = lines[1] if len(lines) > 1 else text

    # Generate sender based on phishing type
    if label == 1:  # Phishing
        if 'credential' in phishing_type.lower():
            sender = "security-alert@verify-account.com"
        elif 'authority' in phishing_type.lower():
            sender = "admin@official-notice.com"
        elif 'romance' in phishing_type.lower() or 'dating' in phishing_type.lower():
            sender = "friend@meetme.com"
        elif 'financial' in phishing_type.lower():
            sender = "prize@winner-notification.com"
        else:
            sender = "noreply@suspicious-domain.com"
    else:  # Legitimate
        sender = "notifications@bank.com"

    return {
        'subject': subject,
        'body': body,
        'sender': sender,
        'label': label,
        'phishing_type': phishing_type,
        'is_phishing': label == 1
    }

def send_email(smtp_server, email_data):
    """Send a single email via SMTP"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = email_data['subject']
        msg['From'] = email_data['sender']
        msg['To'] = f"customer{datetime.now().timestamp()}@bank.com"
        msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

        # Add custom headers for tracking
        msg['X-Email-Label'] = str(email_data['label'])
        msg['X-Phishing-Type'] = email_data['phishing_type']

        # Add body
        body = MIMEText(email_data['body'], 'plain')
        msg.attach(body)

        # Send email
        smtp_server.send_message(msg)

        return True

    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

def load_emails_from_dataset(dataset_path, limit=None):
    """Load emails from CSV dataset"""
    emails = []
    try:
        with open(dataset_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                try:
                    email_data = parse_email_from_csv_row(row)
                    emails.append(email_data)
                except Exception as e:
                    logger.warning(f"Error parsing row {i}: {e}")
                    continue
        logger.info(f"Loaded {len(emails)} emails from dataset")
        return emails
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise

def main():
    """Main seeding function"""
    logger.info(f"Starting email seeder from Kaggle dataset...")
    logger.info(f"Dataset: {DATASET_PATH}")
    logger.info(f"Target: {NUM_EMAILS} emails from dataset")
    logger.info(f"MailPit SMTP: {SMTP_HOST}:{SMTP_PORT}")

    # Wait for MailPit to be ready
    logger.info("Waiting 10 seconds for MailPit to be ready...")
    time.sleep(10)

    # Load emails from dataset
    logger.info(f"Loading emails from dataset...")
    emails = load_emails_from_dataset(DATASET_PATH, limit=NUM_EMAILS)

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
        total_emails = len(emails)
        for batch_num in range(0, total_emails, BATCH_SIZE):
            batch_end = min(batch_num + BATCH_SIZE, total_emails)
            logger.info(f"Sending batch {batch_num//BATCH_SIZE + 1}: emails {batch_num+1}-{batch_end}")

            for i in range(batch_num, batch_end):
                email_data = emails[i]

                # Send email
                if send_email(smtp_server, email_data):
                    sent_count += 1
                    if email_data['is_phishing']:
                        phishing_count += 1
                    else:
                        legitimate_count += 1

                    if (i + 1) % 100 == 0:
                        logger.info(f"Progress: {i + 1}/{total_emails} emails sent")
                else:
                    failed_count += 1

            # Delay between batches
            if batch_end < total_emails:
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
