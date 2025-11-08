#!/bin/bash

echo "🚀 Testing Advanced Collaboration Patterns"
echo "==========================================="
echo ""
echo "Submitting phishing email for analysis..."
echo ""

# Submit the test
RESPONSE=$(curl -s -X POST http://localhost:8000/api/agentic/direct-query \
  -H "Content-Type: application/json" \
  -d '{
    "team": "fraud",
    "query": "URGENT: Your account has been compromised.\n\nFrom: security@paypa1-security.com\nSubject: Immediate Action Required - Account Suspended\n\nDear valued customer,\n\nWe have detected suspicious activity on your PayPal account. Your account has been temporarily suspended for your protection.\n\nTo restore access, please verify your identity immediately by clicking the link below:\nhttp://paypa1-verify.tk/login?ref=12345\n\nYou must complete verification within 24 hours or your account will be permanently closed.\n\nSecurity Team\nPayPal (Not affiliated with PayPal Inc.)"
  }')

echo "$RESPONSE" | python3 -m json.tool

# Extract task ID
TASK_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))" 2>/dev/null)

if [ -z "$TASK_ID" ]; then
    echo "❌ Failed to get task ID"
    exit 1
fi

echo ""
echo "✅ Test submitted! Task ID: $TASK_ID"
echo ""
echo "📊 Monitoring agents (press Ctrl+C to stop)..."
echo "=============================================="
echo ""

# Monitor logs for this specific task
docker compose logs backend -f 2>&1 | grep --line-buffered -E "(Task $TASK_ID|doer|checker|debate|iteration|Deep Analysis)" &
LOG_PID=$!

# Wait 60 seconds or until user stops
sleep 60

# Stop log monitoring
kill $LOG_PID 2>/dev/null

echo ""
echo "🔍 Checking final results..."
echo "============================"
echo ""

# Get final results
curl -s "http://localhost:8000/api/agentic/tasks/$TASK_ID" | python3 -m json.tool | head -150

echo ""
echo "📱 View full results in UI:"
echo "   http://localhost:8080/pages/agentic-teams.html?team=fraud"
echo ""
