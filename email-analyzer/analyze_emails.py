#!/usr/bin/env python3
"""
Email Analyzer Service
Processes emails sequentially, running both analysis and enrichment for each email.
"""

import os
import sys
import time
import requests
from datetime import datetime

# Configuration
BACKEND_HOST = os.getenv('BACKEND_HOST', 'backend')
BACKEND_PORT = os.getenv('BACKEND_PORT', '8000')
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))  # Number of emails to process in one run
PROCESS_DELAY = int(os.getenv('PROCESS_DELAY', '2'))  # Delay between emails (seconds)
CONTINUOUS_MODE = os.getenv('CONTINUOUS_MODE', 'false').lower() == 'true'
LOOP_DELAY = int(os.getenv('LOOP_DELAY', '300'))  # Delay between batch runs (seconds)

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def wait_for_backend():
    """Wait for backend to be ready"""
    log("Waiting for backend to be ready...")
    max_retries = 30
    retry_count = 0

    while retry_count < max_retries:
        try:
            response = requests.get(f"{BACKEND_URL}/api/statistics", timeout=5)
            if response.status_code == 200:
                log("Backend is ready!")
                return True
        except requests.exceptions.RequestException:
            pass

        retry_count += 1
        log(f"Backend not ready yet, retrying... ({retry_count}/{max_retries})")
        time.sleep(2)

    log("ERROR: Backend did not become ready in time")
    return False

def get_unprocessed_emails(limit=100):
    """Fetch emails that haven't been processed yet"""
    try:
        # Get unprocessed emails only (processed=false filter)
        response = requests.get(
            f"{BACKEND_URL}/api/emails",
            params={'limit': limit, 'offset': 0, 'processed': False},
            timeout=30
        )

        if response.status_code != 200:
            log(f"ERROR: Failed to fetch emails: {response.status_code}")
            return []

        emails = response.json()

        # Filter for emails that need processing or enrichment
        unprocessed = []
        for email in emails:
            # Check if email needs processing or enrichment
            needs_processing = not email.get('processed', False)
            needs_enrichment = not email.get('enriched', False)

            if needs_processing or needs_enrichment:
                unprocessed.append({
                    'id': email['id'],
                    'subject': email.get('subject', 'No subject')[:60],
                    'needs_processing': needs_processing,
                    'needs_enrichment': needs_enrichment
                })

        return unprocessed

    except requests.exceptions.RequestException as e:
        log(f"ERROR: Exception fetching emails: {e}")
        return []

def run_analysis(email_id):
    """Run analysis workflows on an email"""
    try:
        log(f"  → Running analysis workflows...")
        response = requests.post(
            f"{BACKEND_URL}/api/emails/{email_id}/process",
            timeout=600  # 10 minutes timeout for analysis (includes slow Ollama LLM processing)
        )

        if response.status_code == 200:
            result = response.json()
            workflows_run = result.get('workflows_run', 0)
            log(f"  ✓ Analysis complete: {workflows_run} workflows executed")
            return True
        elif response.status_code == 404:
            log(f"  ✗ Analysis failed: HTTP 404 - Email not found (may need to refresh email list)")
            return None  # Special return value to indicate 404
        else:
            log(f"  ✗ Analysis failed: HTTP {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        log(f"  ✗ Analysis exception: {e}")
        return False

def run_enrichment(email_id):
    """Run wiki enrichment on an email"""
    try:
        log(f"  → Running wiki enrichment...")
        response = requests.post(
            f"{BACKEND_URL}/api/emails/{email_id}/enrich",
            timeout=60  # 1 minute timeout for enrichment
        )

        if response.status_code == 200:
            result = response.json()
            keywords_count = len(result.get('enriched_keywords', []))
            pages_count = len(result.get('relevant_pages', []))
            log(f"  ✓ Enrichment complete: {keywords_count} keywords from {pages_count} wiki pages")
            return True
        elif response.status_code == 404:
            log(f"  ✗ Enrichment failed: HTTP 404 - Email not found (may need to refresh email list)")
            return None  # Special return value to indicate 404
        else:
            log(f"  ✗ Enrichment failed: HTTP {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        log(f"  ✗ Enrichment exception: {e}")
        return False

def process_email(email_info):
    """Process a single email with both analysis and enrichment"""
    email_id = email_info['id']
    subject = email_info['subject']
    needs_processing = email_info['needs_processing']
    needs_enrichment = email_info['needs_enrichment']

    log(f"\n{'='*70}")
    log(f"Processing Email ID: {email_id}")
    log(f"Subject: {subject}")
    log(f"Needs Analysis: {needs_processing} | Needs Enrichment: {needs_enrichment}")
    log(f"{'='*70}")

    success = True
    got_404 = False

    # Run analysis if needed
    if needs_processing:
        result = run_analysis(email_id)
        if result is None:  # 404 error
            got_404 = True
        elif not result:
            success = False
    else:
        log(f"  ⊘ Analysis skipped (already processed)")

    # Run enrichment if needed (skip if we got 404)
    if needs_enrichment and not got_404:
        result = run_enrichment(email_id)
        if result is None:  # 404 error
            got_404 = True
        elif not result:
            success = False
    elif not got_404:
        log(f"  ⊘ Enrichment skipped (already enriched)")

    # Return None if we got 404 (email doesn't exist), otherwise return success status
    return None if got_404 else success

def run_batch():
    """Process a batch of unprocessed emails"""
    log("\n" + "="*70)
    log("STARTING EMAIL ANALYSIS BATCH")
    log("="*70)

    # Fetch unprocessed emails
    log(f"\nFetching up to {BATCH_SIZE} unprocessed emails...")
    emails = get_unprocessed_emails(limit=BATCH_SIZE)

    if not emails:
        log("No unprocessed emails found. All emails are up to date!")
        return 0

    log(f"Found {len(emails)} emails to process\n")

    # Process each email sequentially
    processed_count = 0
    failed_count = 0

    for idx, email_info in enumerate(emails, 1):
        log(f"\n[{idx}/{len(emails)}] Processing email...")

        try:
            success = process_email(email_info)

            if success is None:  # Got 404 - email doesn't exist
                log(f"\n⚠ Email not found (404) - breaking batch to refresh email list")
                failed_count += 1
                break  # Exit the loop early to fetch fresh emails
            elif success:
                processed_count += 1
            else:
                failed_count += 1

            # Delay between emails to avoid overwhelming the system
            if idx < len(emails):
                log(f"\nWaiting {PROCESS_DELAY} seconds before next email...")
                time.sleep(PROCESS_DELAY)

        except Exception as e:
            log(f"ERROR: Unexpected exception processing email {email_info['id']}: {e}")
            failed_count += 1

    # Summary
    log("\n" + "="*70)
    log("BATCH PROCESSING COMPLETE")
    log("="*70)
    log(f"Total Processed: {processed_count}")
    log(f"Total Failed: {failed_count}")
    log(f"Total Emails: {len(emails)}")
    log("="*70 + "\n")

    return processed_count

def main():
    """Main entry point"""
    log("="*70)
    log("EMAIL ANALYZER SERVICE STARTING")
    log("="*70)
    log(f"Backend URL: {BACKEND_URL}")
    log(f"Batch Size: {BATCH_SIZE}")
    log(f"Process Delay: {PROCESS_DELAY}s")
    log(f"Continuous Mode: {CONTINUOUS_MODE}")
    if CONTINUOUS_MODE:
        log(f"Loop Delay: {LOOP_DELAY}s")
    log("="*70 + "\n")

    # Wait for backend to be ready
    if not wait_for_backend():
        log("FATAL: Backend not available, exiting")
        sys.exit(1)

    if CONTINUOUS_MODE:
        # Continuous mode: keep processing in a loop
        log("Running in CONTINUOUS mode - will process emails in batches repeatedly\n")

        while True:
            try:
                processed = run_batch()

                if processed == 0:
                    log(f"No emails to process. Waiting {LOOP_DELAY} seconds before checking again...")
                else:
                    log(f"Batch complete. Waiting {LOOP_DELAY} seconds before next batch...")

                time.sleep(LOOP_DELAY)

            except KeyboardInterrupt:
                log("\nReceived interrupt signal, shutting down gracefully...")
                break
            except Exception as e:
                log(f"ERROR: Unexpected exception in main loop: {e}")
                log(f"Waiting {LOOP_DELAY} seconds before retrying...")
                time.sleep(LOOP_DELAY)
    else:
        # One-time mode: process once and exit
        log("Running in ONE-TIME mode - will process one batch and exit\n")
        processed = run_batch()

        if processed > 0:
            log(f"✓ Successfully processed {processed} emails")
            sys.exit(0)
        else:
            log("No emails were processed")
            sys.exit(0)

if __name__ == "__main__":
    main()
