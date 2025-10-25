#!/bin/bash

# Find emails to test RAG enrichment
# Usage: ./find_test_emails.sh

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          FIND EMAILS FOR RAG ENRICHMENT TESTING                ║"
echo "╚════════════════════════════════════════════════════════════════╝"

echo -e "\n📋 Legitimate Emails (first 20):\n"
echo "ID   | Subject                                           | Enriched"
echo "─────┼───────────────────────────────────────────────────┼─────────"

curl -s "http://localhost:8000/api/emails?limit=20&label=0" | python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)
    for email in data:
        email_id = email['id']
        subject = email['subject'][:50].ljust(50)
        enriched = '✓' if email.get('enriched') else '✗'
        print(f'{email_id:4d} | {subject} | {enriched}')
except Exception as e:
    print(f'Error: {e}')
"

echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "To test an email, run: ./test_rag_enrichment.sh <email_id>"
echo "Example: ./test_rag_enrichment.sh 113"
