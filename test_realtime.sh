#!/bin/bash

# Test Real-Time Investment Analysis with SSE
# Usage: ./test_realtime.sh TICKER
# Example: ./test_realtime.sh AAPL

TICKER="${1:-AAPL}"

echo "========================================"
echo "Real-Time Investment Analysis Test"
echo "========================================"
echo ""
echo "Testing with: $TICKER"
echo ""

# Submit analysis
echo "1. Submitting analysis request..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/agentic/direct-query \
  -H "Content-Type: application/json" \
  -d "{\"team\": \"investments\", \"query\": \"$TICKER\"}")

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
timeout 120 curl -N http://localhost:8000/api/events 2>/dev/null | while IFS= read -r line; do
  if [[ $line == data:* ]]; then
    # Extract JSON from SSE data line
    EVENT_JSON="${line#data: }"

    # Parse event
    EVENT_TYPE=$(echo "$EVENT_JSON" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(data.get('type', ''))" 2>/dev/null)

    if [ "$EVENT_TYPE" = "agentic_message" ]; then
      # Check if it's for our task
      MSG_TASK=$(echo "$EVENT_JSON" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(data.get('data', {}).get('task_id', ''))" 2>/dev/null)

      if [ "$MSG_TASK" = "$TASK_ID" ]; then
        # Extract agent role
        ROLE=$(echo "$EVENT_JSON" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(data.get('data', {}).get('message', {}).get('role', ''))" 2>/dev/null)
        ICON=$(echo "$EVENT_JSON" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(data.get('data', {}).get('message', {}).get('icon', ''))" 2>/dev/null)

        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "$ICON $ROLE - Analysis Complete!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
      fi
    elif [ "$EVENT_TYPE" = "agentic_complete" ]; then
      # Check if it's for our task
      COMPLETE_TASK=$(echo "$EVENT_JSON" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(data.get('data', {}).get('task_id', ''))" 2>/dev/null)

      if [ "$COMPLETE_TASK" = "$TASK_ID" ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ ANALYSIS COMPLETE!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "View full results:"
        echo "  http://localhost:8080/pages/agentic-teams.html?team=investments"
        break
      fi
    fi
  fi
done

echo ""
echo "Test complete!"
