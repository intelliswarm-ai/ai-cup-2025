#!/bin/bash

# Test Fraud Detection Workflow with SSE
# Usage: ./test_fraud.sh TRANSACTION_ID USER_ID
# Example: ./test_fraud.sh txn_12345 user_789

TRANSACTION_ID="${1:-txn_suspicious_001}"
USER_ID="${2:-user_12345}"

echo "========================================"
echo "Fraud Detection Analysis Test"
echo "========================================"
echo ""
echo "Testing with:"
echo "  Transaction ID: $TRANSACTION_ID"
echo "  User ID: $USER_ID"
echo ""

# Create query text
QUERY="Suspicious transaction detected. Transaction ID: $TRANSACTION_ID for User: $USER_ID. Large purchase ($2,500) from new merchant 'Online Retailer XYZ' using device from unusual location. Please analyze for fraud."

# Submit analysis
echo "1. Submitting fraud analysis request..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/agentic/direct-query \
  -H "Content-Type: application/json" \
  -d "{\"team\": \"fraud\", \"query\": \"$QUERY\"}")

echo "$RESPONSE" | python3 -m json.tool 2>/dev/null

# Extract task ID
TASK_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))" 2>/dev/null)

if [ -z "$TASK_ID" ]; then
  echo "❌ Failed to create task"
  exit 1
fi

echo ""
echo "✅ Task created: $TASK_ID"
echo ""
echo "2. Open SSE connection and watch for real-time events..."
echo "   (Press Ctrl+C to stop)"
echo ""

# Monitor SSE events for this task
timeout 180 curl -N http://localhost:8000/api/events 2>/dev/null | while IFS= read -r line; do
  if [[ $line == data:* ]]; then
    # Extract JSON from SSE data line
    EVENT_JSON="${line#data: }"

    # Parse event
    EVENT_TYPE=$(echo "$EVENT_JSON" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(data.get('type', ''))" 2>/dev/null)

    if [ "$EVENT_TYPE" = "agentic_message" ]; then
      # Check if it's for our task
      MSG_TASK=$(echo "$EVENT_JSON" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(data.get('data', {}).get('task_id', ''))" 2>/dev/null)

      if [ "$MSG_TASK" = "$TASK_ID" ]; then
        # Extract agent role and message
        ROLE=$(echo "$EVENT_JSON" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(data.get('data', {}).get('message', {}).get('role', ''))" 2>/dev/null)
        ICON=$(echo "$EVENT_JSON" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(data.get('data', {}).get('message', {}).get('icon', ''))" 2>/dev/null)
        IS_THINKING=$(echo "$EVENT_JSON" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(data.get('data', {}).get('message', {}).get('is_thinking', False))" 2>/dev/null)
        TEXT=$(echo "$EVENT_JSON" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(data.get('data', {}).get('message', {}).get('text', '')[:200])" 2>/dev/null)

        if [ "$IS_THINKING" = "True" ]; then
          echo "💭 $ICON $ROLE: $TEXT..."
        else
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          echo "$ICON $ROLE - Analysis Complete!"
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          echo ""
        fi
      fi
    elif [ "$EVENT_TYPE" = "agentic_complete" ]; then
      # Check if it's for our task
      COMPLETE_TASK=$(echo "$EVENT_JSON" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(data.get('data', {}).get('task_id', ''))" 2>/dev/null)

      if [ "$COMPLETE_TASK" = "$TASK_ID" ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ FRAUD ANALYSIS COMPLETE!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "View full results:"
        echo "  http://localhost:8080/pages/agentic-teams.html?team=fraud"
        echo ""
        echo "Get task details:"
        echo "  curl http://localhost:8000/api/agentic/task/$TASK_ID"
        break
      fi
    fi
  fi
done

echo ""
echo "Test complete!"
