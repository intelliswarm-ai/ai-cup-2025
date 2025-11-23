#!/bin/bash

# Agentic Workflows - Comprehensive Test Script
# This script tests all three agentic workflows (Investments, Fraud, Compliance)
# and verifies that the backend, SSE events, and data structures are working correctly.

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║        🤖 Agentic Workflows - Comprehensive Test Suite 🤖       ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "  Testing: $test_name... "

    if eval "$test_command" | grep -q "$expected_pattern"; then
        echo -e "${GREEN}✓ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Wait for workflow completion
wait_for_workflow() {
    local email_id="$1"
    local max_wait=120  # 2 minutes max
    local waited=0

    echo -n "    Waiting for workflow to complete (email $email_id)..."

    while [ $waited -lt $max_wait ]; do
        if curl -s "http://localhost:8000/api/emails/$email_id" | grep -q '"processed": true'; then
            echo -e " ${GREEN}✓ Completed in ${waited}s${NC}"
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
        echo -n "."
    done

    echo -e " ${RED}✗ Timeout after ${max_wait}s${NC}"
    return 1
}

echo "════════════════════════════════════════════════════════════════════"
echo " 1️⃣  Backend Health Checks"
echo "════════════════════════════════════════════════════════════════════"
echo ""

run_test "Backend API is accessible" \
    "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/emails?limit=1" \
    "200"

run_test "Frontend is accessible (HTTPS)" \
    "curl -s -o /dev/null -w '%{http_code}' -k https://localhost/" \
    "200"

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo " 2️⃣  Investment Team Workflow Test"
echo "════════════════════════════════════════════════════════════════════"
echo ""

echo "  📊 Submitting investment query..."
INVESTMENT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/agentic/direct-query \
    -H "Content-Type: application/json" \
    -d '{"team": "investments", "query": "Quick analysis of NVDA stock for testing"}')

INVESTMENT_EMAIL_ID=$(echo "$INVESTMENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('email_id', ''))")
INVESTMENT_TASK_ID=$(echo "$INVESTMENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))")

if [ -z "$INVESTMENT_EMAIL_ID" ]; then
    echo -e "  ${RED}✗ Failed to create investment query${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "  ${GREEN}✓ Created email $INVESTMENT_EMAIL_ID, task $INVESTMENT_TASK_ID${NC}"

    # Wait for completion
    if wait_for_workflow "$INVESTMENT_EMAIL_ID"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Verify message count
        MESSAGE_COUNT=$(curl -s "http://localhost:8000/api/emails/$INVESTMENT_EMAIL_ID" | grep -o '"role":' | wc -l)
        if [ "$MESSAGE_COUNT" -eq 4 ]; then
            echo -e "  ${GREEN}✓ Investment workflow has 4 messages (expected)${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "  ${RED}✗ Investment workflow has $MESSAGE_COUNT messages (expected 4)${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo " 3️⃣  Fraud Detection Team Workflow Test"
echo "════════════════════════════════════════════════════════════════════"
echo ""

echo "  🔍 Submitting fraud detection query..."
FRAUD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/agentic/direct-query \
    -H "Content-Type: application/json" \
    -d '{"team": "fraud", "query": "Test suspicious activity detection"}')

FRAUD_EMAIL_ID=$(echo "$FRAUD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('email_id', ''))")
FRAUD_TASK_ID=$(echo "$FRAUD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))")

if [ -z "$FRAUD_EMAIL_ID" ]; then
    echo -e "  ${RED}✗ Failed to create fraud query${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "  ${GREEN}✓ Created email $FRAUD_EMAIL_ID, task $FRAUD_TASK_ID${NC}"

    # Wait for completion
    if wait_for_workflow "$FRAUD_EMAIL_ID"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Verify message count
        MESSAGE_COUNT=$(curl -s "http://localhost:8000/api/emails/$FRAUD_EMAIL_ID" | grep -o '"role":' | wc -l)
        if [ "$MESSAGE_COUNT" -eq 4 ]; then
            echo -e "  ${GREEN}✓ Fraud workflow has 4 messages (expected)${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "  ${RED}✗ Fraud workflow has $MESSAGE_COUNT messages (expected 4)${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo " 4️⃣  Compliance Team Workflow Test"
echo "════════════════════════════════════════════════════════════════════"
echo ""

echo "  ⚖️  Submitting compliance query..."
COMPLIANCE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/agentic/direct-query \
    -H "Content-Type: application/json" \
    -d '{"team": "compliance", "query": "Test KYC verification process"}')

COMPLIANCE_EMAIL_ID=$(echo "$COMPLIANCE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('email_id', ''))")
COMPLIANCE_TASK_ID=$(echo "$COMPLIANCE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))")

if [ -z "$COMPLIANCE_EMAIL_ID" ]; then
    echo -e "  ${RED}✗ Failed to create compliance query${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "  ${GREEN}✓ Created email $COMPLIANCE_EMAIL_ID, task $COMPLIANCE_TASK_ID${NC}"

    # Wait for completion
    if wait_for_workflow "$COMPLIANCE_EMAIL_ID"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Verify message count (compliance has more messages due to multi-stage analysis)
        MESSAGE_COUNT=$(curl -s "http://localhost:8000/api/emails/$COMPLIANCE_EMAIL_ID" | grep -o '"role":' | wc -l)
        if [ "$MESSAGE_COUNT" -ge 4 ]; then
            echo -e "  ${GREEN}✓ Compliance workflow has $MESSAGE_COUNT messages (expected 4+)${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "  ${RED}✗ Compliance workflow has $MESSAGE_COUNT messages (expected 4+)${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo " 5️⃣  SSE Event Broadcasting Verification"
echo "════════════════════════════════════════════════════════════════════"
echo ""

# Check recent backend logs for SSE broadcasts
SSE_MESSAGE_COUNT=$(docker-compose logs backend --tail 200 | grep "Broadcasting event: agentic_message" | wc -l)
SSE_COMPLETE_COUNT=$(docker-compose logs backend --tail 200 | grep "Broadcasting event: agentic_complete" | wc -l)

if [ "$SSE_MESSAGE_COUNT" -gt 0 ]; then
    echo -e "  ${GREEN}✓ Found $SSE_MESSAGE_COUNT SSE message broadcasts${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "  ${RED}✗ No SSE message broadcasts found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

if [ "$SSE_COMPLETE_COUNT" -gt 0 ]; then
    echo -e "  ${GREEN}✓ Found $SSE_COMPLETE_COUNT SSE completion broadcasts${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "  ${RED}✗ No SSE completion broadcasts found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo " 6️⃣  Data Structure Verification"
echo "════════════════════════════════════════════════════════════════════"
echo ""

if [ ! -z "$INVESTMENT_EMAIL_ID" ]; then
    # Check if workflow_name starts with "agentic_"
    WORKFLOW_NAME=$(curl -s "http://localhost:8000/api/emails/$INVESTMENT_EMAIL_ID" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('workflow_results', [{}])[0].get('workflow_name', '') if data.get('workflow_results') else '')" 2>/dev/null || echo "")

    if echo "$WORKFLOW_NAME" | grep -q "^agentic_"; then
        echo -e "  ${GREEN}✓ Workflow name follows pattern 'agentic_*'${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}✗ Workflow name pattern mismatch: $WORKFLOW_NAME${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Check if result has discussion.messages structure
    HAS_MESSAGES=$(curl -s "http://localhost:8000/api/emails/$INVESTMENT_EMAIL_ID" | python3 -c "import sys, json; data=json.load(sys.stdin); wr=data.get('workflow_results', [{}])[0] if data.get('workflow_results') else {}; print('yes' if wr.get('result', {}).get('discussion', {}).get('messages') else 'no')" 2>/dev/null || echo "no")

    if [ "$HAS_MESSAGES" = "yes" ]; then
        echo -e "  ${GREEN}✓ Email has correct data structure (result.discussion.messages)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}✗ Email missing discussion messages structure${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo " 📊 Test Summary"
echo "════════════════════════════════════════════════════════════════════"
echo ""

echo "  Total Tests Run:    $TESTS_RUN"
echo -e "  ${GREEN}Tests Passed:      $TESTS_PASSED${NC}"
echo -e "  ${RED}Tests Failed:      $TESTS_FAILED${NC}"
echo ""

# Calculate success rate
if [ $TESTS_RUN -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=1; $TESTS_PASSED * 100 / $TESTS_RUN" | bc)
    echo "  Success Rate:      ${SUCCESS_RATE}%"
else
    echo "  Success Rate:      N/A"
fi

echo ""
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                  ║${NC}"
    echo -e "${GREEN}║                  ✅ ALL TESTS PASSED! ✅                         ║${NC}"
    echo -e "${GREEN}║                                                                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                                  ║${NC}"
    echo -e "${RED}║                  ❌ SOME TESTS FAILED ❌                         ║${NC}"
    echo -e "${RED}║                                                                  ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
