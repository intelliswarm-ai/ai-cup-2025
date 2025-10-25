#!/bin/bash

# RAG Enrichment Test Script
# Usage: ./test_rag_enrichment.sh [email_id]

EMAIL_ID=${1:-113}

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              RAG ENRICHMENT TEST SCRIPT                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"

echo -e "\n📧 Testing Email ID: $EMAIL_ID\n"

# Step 1: View email details
echo "─────────────────────────────────────────────────────────────────"
echo "STEP 1: Email Details"
echo "─────────────────────────────────────────────────────────────────"
curl -s "http://localhost:8000/api/emails/$EMAIL_ID" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'Subject: {data[\"subject\"]}')
    print(f'From: {data[\"sender\"]}')
    print(f'To: {data[\"recipient\"]}')
    print(f'Label: {\"LEGITIMATE\" if data.get(\"label\") == 0 else \"PHISHING\" if data.get(\"label\") == 1 else \"Unknown\"}')
except Exception as e:
    print(f'Error: Could not find email {EMAIL_ID}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "\n❌ Email not found. Try another ID."
    echo "To find available emails, run:"
    echo "  curl -s 'http://localhost:8000/api/emails?limit=20&label=0' | python3 -m json.tool"
    exit 1
fi

# Step 2: Run enrichment
echo -e "\n─────────────────────────────────────────────────────────────────"
echo "STEP 2: Running RAG Enrichment"
echo "─────────────────────────────────────────────────────────────────"
curl -s -X POST "http://localhost:8000/api/emails/$EMAIL_ID/enrich" | python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)

    if data.get('status') == 'success':
        print(f'\n✓ Status: SUCCESS')
        print(f'✓ Email ID: {data[\"email_id\"]}')

        # Show relevant pages
        pages = data.get('relevant_pages', [])
        print(f'\n📚 Relevant Wiki Pages ({len(pages)}):')
        for i, page in enumerate(pages, 1):
            print(f'   {i}. {page}')

        # Show enriched keywords
        keywords = data.get('enriched_keywords', [])
        print(f'\n🔑 Enriched Keywords (showing top 5 of {len(keywords)}):')
        print('═' * 70)

        for i, kw in enumerate(keywords[:5], 1):
            print(f'\n{i}. Keyword: \"{kw[\"keyword\"]}\"')
            print(f'   Wiki Page: {kw[\"wiki_page\"]}')
            print(f'   Confidence: {kw[\"confidence\"]}%')
            print(f'   Context Preview:')
            print(f'   \"{kw[\"context\"][:200]}...\"')
            print('   ' + '─' * 66)

        if len(keywords) > 5:
            print(f'\n   ... and {len(keywords) - 5} more keywords')

    elif data.get('status') == 'skipped':
        print(f'\n⚠ Enrichment skipped: {data.get(\"reason\")}')
        print('   (Only legitimate emails can be enriched)')
    else:
        print(f'\n❌ Error: {data}')

except Exception as e:
    print(f'\n❌ Error processing response: {e}')
"

echo -e "\n─────────────────────────────────────────────────────────────────"
echo "✓ Test Complete!"
echo "─────────────────────────────────────────────────────────────────"
echo -e "\nTo test another email: ./test_rag_enrichment.sh <email_id>"
echo "To view OtterWiki: http://localhost:9000"
echo "To view enriched data: Check the database or use the API"
