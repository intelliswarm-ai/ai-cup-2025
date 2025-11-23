#!/bin/bash
# Quick smoke test for critical functionality
# Run this after ANY code change to catch regressions

echo "🧪 Running Critical Path Smoke Tests..."
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

FAILED=0

# Test 1: Backend is running
echo "1. Testing backend health..."
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend health OK${NC}"
else
    echo -e "${RED}❌ Backend not responding${NC}"
    FAILED=1
fi

# Test 2: Frontend is serving
echo "2. Testing frontend..."
if curl -f -s http://localhost/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend OK${NC}"
else
    echo -e "${RED}❌ Frontend not responding${NC}"
    FAILED=1
fi

# Test 3: API endpoints work
echo "3. Testing email API..."
if curl -f -s "http://localhost:8000/api/emails?limit=1" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Email API OK${NC}"
else
    echo -e "${RED}❌ Email API failed${NC}"
    FAILED=1
fi

# Test 4: Dashboard API works
echo "4. Testing dashboard API..."
if curl -f -s http://localhost:8000/api/dashboard/enriched-stats > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Dashboard API OK${NC}"
else
    echo -e "${RED}❌ Dashboard API failed${NC}"
    FAILED=1
fi

# Test 5: Direct query API works
echo "5. Testing direct query API..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/agentic/direct-query \
  -H "Content-Type: application/json" \
  -d '{"team": "investments", "query": "Test query"}')

if echo "$RESPONSE" | grep -q '"task_id"'; then
    echo -e "${GREEN}✅ Direct query API OK${NC}"
else
    echo -e "${RED}❌ Direct query API failed${NC}"
    echo "Response: $RESPONSE"
    FAILED=1
fi

# Test 6: No ground truth in email API responses
echo "6. Testing ground truth removal (emails)..."
RESPONSE=$(curl -s "http://localhost:8000/api/emails?limit=1")
if echo "$RESPONSE" | grep -q '"label"'; then
  echo -e "${RED}❌ Ground truth 'label' field found in email API!${NC}"
  FAILED=1
elif echo "$RESPONSE" | grep -q '"phishing_type"'; then
  echo -e "${RED}❌ Ground truth 'phishing_type' field found in email API!${NC}"
  FAILED=1
else
  echo -e "${GREEN}✅ Ground truth properly removed from emails${NC}"
fi

# Test 7: No ground truth in dashboard API responses
echo "7. Testing ground truth removal (dashboard)..."
RESPONSE=$(curl -s http://localhost:8000/api/dashboard/enriched-stats)
if echo "$RESPONSE" | grep -q '"ground_truth_phishing"'; then
  echo -e "${RED}❌ Ground truth 'ground_truth_phishing' found in dashboard API!${NC}"
  FAILED=1
elif echo "$RESPONSE" | grep -q '"ground_truth_legitimate"'; then
  echo -e "${RED}❌ Ground truth 'ground_truth_legitimate' found in dashboard API!${NC}"
  FAILED=1
else
  echo -e "${GREEN}✅ Ground truth properly removed from dashboard${NC}"
fi

# Test 8: Team tools endpoints work
echo "8. Testing team tools APIs..."
INVESTMENT_TOOLS=$(curl -s "http://localhost:8000/api/teams/investments/tools")
if echo "$INVESTMENT_TOOLS" | grep -q '"name"'; then
    echo -e "${GREEN}✅ Investment team tools OK${NC}"
else
    echo -e "${RED}❌ Investment team tools failed${NC}"
    FAILED=1
fi

FRAUD_TOOLS=$(curl -s "http://localhost:8000/api/teams/fraud/tools")
if echo "$FRAUD_TOOLS" | grep -q '"name"'; then
    echo -e "${GREEN}✅ Fraud team tools OK${NC}"
else
    echo -e "${RED}❌ Fraud team tools failed${NC}"
    FAILED=1
fi

COMPLIANCE_TOOLS=$(curl -s "http://localhost:8000/api/teams/compliance/tools")
if echo "$COMPLIANCE_TOOLS" | grep -q '"name"'; then
    echo -e "${GREEN}✅ Compliance team tools OK${NC}"
else
    echo -e "${RED}❌ Compliance team tools failed${NC}"
    FAILED=1
fi

echo ""
echo "========================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All smoke tests passed!${NC}"
    echo ""
    echo "📝 Next: Run manual regression checklist"
    echo "   See: DIRECT_QUERY_FIX_AND_REGRESSION_PREVENTION.md"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    echo "Please fix the issues before committing."
    exit 1
fi
