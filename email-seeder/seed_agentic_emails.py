#!/usr/bin/env python3
"""
Agentic Workflow Email Seeder
Seeds specialized emails designed to trigger virtual bank team discussions
"""

import csv
import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Configuration
SMTP_HOST = os.getenv('MAILPIT_SMTP_HOST', 'localhost')
SMTP_PORT = int(os.getenv('MAILPIT_SMTP_PORT', 1025))
DATASET_PATH = os.getenv('DATASET_PATH', 'dataset/agentic_workflow_emails.csv')

# Team routing keywords for demonstration
TEAM_ROUTING = {
    'credit': '🏦 Credit Risk Committee',
    'fraud': '🔍 Fraud Investigation Unit',
    'compliance': '⚖️ Compliance & Regulatory Affairs',
    'wealth': '💼 Wealth Management Advisory',
    'corporate': '🏢 Corporate Banking Team',
    'operations': '⚙️ Operations & Quality',
}

def detect_team(email_text):
    """Detect which team should handle this email based on content"""
    text_lower = email_text.lower()

    if any(word in text_lower for word in ['credit line', 'loan', 'credit increase', 'financing']):
        return '🏦 Credit Risk Committee'
    elif any(word in text_lower for word in ['fraud', 'suspicious', 'wire transfer', 'phishing', 'bec']):
        return '🔍 Fraud Investigation Unit'
    elif any(word in text_lower for word in ['compliance', 'regulatory', 'fatca', 'regulation', 'legal']):
        return '⚖️ Compliance & Regulatory Affairs'
    elif any(word in text_lower for word in ['wealth', 'investment', 'portfolio', 'inheritance', 'estate']):
        return '💼 Wealth Management Advisory'
    elif any(word in text_lower for word in ['corporate', 'trade finance', 'letter of credit', 'import', 'export']):
        return '🏢 Corporate Banking Team'
    elif any(word in text_lower for word in ['complaint', 'customer service', 'quality', 'operations']):
        return '⚙️ Operations & Quality'
    else:
        return '📋 General Banking'

def send_email(smtp, subject, body, from_email, to_email, team_assigned):
    """Send a single email via SMTP"""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')

    # Add custom header to indicate team assignment
    msg['X-Team-Assignment'] = team_assigned
    msg['X-Agentic-Workflow'] = 'true'

    # Create both plain text and HTML versions
    text_part = MIMEText(body, 'plain')
    html_body = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
          .team-badge {{
            background-color: #2196F3;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            display: inline-block;
            margin-bottom: 10px;
          }}
          .email-content {{
            white-space: pre-wrap;
            padding: 20px;
            background-color: #f5f5f5;
            border-left: 4px solid #2196F3;
          }}
        </style>
      </head>
      <body>
        <div class="team-badge">🤖 {team_assigned}</div>
        <div class="email-content">{body}</div>
      </body>
    </html>
    """
    html_part = MIMEText(html_body, 'html')

    msg.attach(text_part)
    msg.attach(html_part)

    smtp.send_message(msg)

def extract_email_parts(email_text):
    """Extract subject, from, to, and body from email text"""
    lines = email_text.split('\n')

    subject = ""
    from_email = ""
    to_email = ""
    body_lines = []

    in_body = False

    for line in lines:
        if line.startswith('Subject:'):
            subject = line.replace('Subject:', '').strip()
        elif line.startswith('From:'):
            from_email = line.replace('From:', '').strip()
        elif line.startswith('To:'):
            to_email = line.replace('To:', '').strip()
            in_body = True
        elif in_body:
            body_lines.append(line)

    body = '\n'.join(body_lines).strip()

    # Default values if not found
    if not from_email:
        from_email = "customer@bank.com"
    if not to_email:
        to_email = "banking@swissbank.ch"
    if not subject:
        subject = "Banking Inquiry"

    return subject, from_email, to_email, body

def main():
    print("=" * 60)
    print("🤖 Agentic Workflow Email Seeder")
    print("=" * 60)
    print(f"SMTP Server: {SMTP_HOST}:{SMTP_PORT}")
    print(f"Dataset: {DATASET_PATH}")
    print()

    # Read the CSV file
    emails_sent = 0

    try:
        with open(DATASET_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Connect to SMTP server
            print(f"Connecting to MailPit at {SMTP_HOST}:{SMTP_PORT}...")
            smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT)

            print(f"✓ Connected to SMTP server")
            print()

            for idx, row in enumerate(reader, 1):
                email_text = row['text']
                label = row['label']
                phishing_type = row.get('phishing_type', 'legitimate')

                # Extract email components
                subject, from_email, to_email, body = extract_email_parts(email_text)

                # Detect which team should handle this
                team_assigned = detect_team(email_text)

                # Send email
                print(f"📧 Email {idx}: {subject[:50]}...")
                print(f"   From: {from_email}")
                print(f"   Team: {team_assigned}")

                try:
                    send_email(smtp, subject, body, from_email, to_email, team_assigned)
                    emails_sent += 1
                    print(f"   ✓ Sent successfully")
                except Exception as e:
                    print(f"   ✗ Error: {e}")

                print()

                # Small delay to avoid overwhelming the server
                time.sleep(0.5)

            smtp.quit()

    except FileNotFoundError:
        print(f"✗ Error: Dataset file not found: {DATASET_PATH}")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("=" * 60)
    print(f"✅ Seeding complete!")
    print(f"   Total emails sent: {emails_sent}")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    exit(main())
