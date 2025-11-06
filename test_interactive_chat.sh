#!/bin/bash

# Test Interactive Chat with Investment Team

echo "Testing Interactive Investment Team Chat..."
echo "=========================================="

API_BASE="http://localhost:8000/api"

# Step 1: Create a direct query to start the investment analysis
echo ""
echo "1. Starting investment analysis for TSLA..."
QUERY_RESPONSE=$(curl -s -X POST "$API_BASE/agentic/direct-query" \
  -H "Content-Type: application/json" \
  -d '{
    "team": "investments",
    "query": "TSLA"
  }')

TASK_ID=$(echo $QUERY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['task_id'])" 2>/dev/null)
EMAIL_ID=$(echo $QUERY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['email_id'])" 2>/dev/null)

if [ -z "$TASK_ID" ]; then
  echo "❌ Failed to start analysis"
  echo "Response: $QUERY_RESPONSE"
  exit 1
fi

echo "✓ Analysis started with task_id: $TASK_ID"

# Step 2: Wait a few seconds for analysis to start
echo ""
echo "2. Waiting for analysis to start..."
sleep 5

# Step 3: Check task status
echo ""
echo "3. Checking task status..."
TASK_STATUS=$(curl -s "$API_BASE/agentic/tasks/$TASK_ID")
echo "Task status: $(echo $TASK_STATUS | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Status: {d.get('status', 'unknown')}, Messages: {len(d.get('result', {}).get('discussion', {}).get('messages', []))}\")" 2>/dev/null)"

# Step 4: Send a chat message to the team
echo ""
echo "4. Sending chat message to the team..."
CHAT_RESPONSE=$(curl -s -X POST "$API_BASE/agentic/task/$TASK_ID/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What about the debt levels?"
  }')

echo "Chat response:"
echo $CHAT_RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Agent: {d.get('agent')}\"); print(f\"Response: {d.get('response')}\")" 2>/dev/null

# Step 5: Wait for analysis to complete
echo ""
echo "5. Waiting for analysis to complete (30 seconds)..."
sleep 30

# Step 6: Check final status
echo ""
echo "6. Checking final task status..."
FINAL_STATUS=$(curl -s "$API_BASE/agentic/tasks/$TASK_ID")
echo "Final status: $(echo $FINAL_STATUS | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Status: {d.get('status', 'unknown')}, Total Messages: {len(d.get('result', {}).get('discussion', {}).get('messages', []))}\")" 2>/dev/null)"

echo ""
echo "=========================================="
echo "✓ Test completed!"
echo ""
echo "To view the full analysis, open:"
echo "http://localhost:8000/pages/agentic-teams.html?team=investments"
