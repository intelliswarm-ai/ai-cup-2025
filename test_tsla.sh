#!/bin/bash

# Test TSLA stock analysis via API
echo "Testing TSLA stock analysis..."
echo ""

# Create the analysis task
RESPONSE=$(curl -s -X POST http://localhost:8000/api/agentic/direct-query \
  -H "Content-Type: application/json" \
  -d '{
    "team": "investments",
    "query": "Please provide complete stock analysis for TSLA (Tesla)"
  }')

echo "Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

# Extract task_id
TASK_ID=$(echo "$RESPONSE" | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TASK_ID" ]; then
  echo ""
  echo "Task created with ID: $TASK_ID"
  echo ""
  echo "To view results, visit:"
  echo "  http://localhost:8080/pages/agentic-teams.html"
  echo ""
  echo "Or check task status with:"
  echo "  curl http://localhost:8000/api/agentic/task/$TASK_ID"
fi
