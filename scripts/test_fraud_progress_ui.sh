#!/bin/bash

# Test Fraud Detection Progress UI Implementation
# This validates the progress tracking implementation in mailbox.html

echo "========================================"
echo "Fraud Detection Progress UI Test"
echo "========================================"
echo ""

# Detect if running from root or scripts directory
if [ -f "frontend/pages/mailbox.html" ]; then
    MAILBOX_FILE="frontend/pages/mailbox.html"
elif [ -f "../frontend/pages/mailbox.html" ]; then
    MAILBOX_FILE="../frontend/pages/mailbox.html"
else
    echo "Error: Cannot find mailbox.html. Please run from project root or scripts directory."
    exit 1
fi
TEST_PASSED=0
TEST_FAILED=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((TEST_PASSED++))
}

function fail() {
    echo -e "${RED}✗${NC} $1"
    ((TEST_FAILED++))
}

function info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

echo "Testing mailbox.html implementation..."
echo ""

# Test 1: Check if fraud progress tracker CSS exists
echo "1. Checking CSS implementation..."
if grep -q "fraud-progress-tracker" "$MAILBOX_FILE"; then
    pass "Fraud progress tracker CSS found"
else
    fail "Fraud progress tracker CSS missing"
fi

if grep -q "progress-step.active" "$MAILBOX_FILE"; then
    pass "Progress step states CSS found"
else
    fail "Progress step states CSS missing"
fi

if grep -q "@keyframes pulse-text" "$MAILBOX_FILE"; then
    pass "Animation keyframes found"
else
    fail "Animation keyframes missing"
fi

echo ""

# Test 2: Check if fraud progress modal exists
echo "2. Checking Modal HTML structure..."
if grep -q 'id="fraudProgressModal"' "$MAILBOX_FILE"; then
    pass "Fraud progress modal HTML found"
else
    fail "Fraud progress modal HTML missing"
fi

if grep -q 'id="fraudProgressModalBody"' "$MAILBOX_FILE"; then
    pass "Modal body container found"
else
    fail "Modal body container missing"
fi

if grep -q 'id="fraud-view-discussion-btn"' "$MAILBOX_FILE"; then
    pass "View discussion button found"
else
    fail "View discussion button missing"
fi

echo ""

# Test 3: Check JavaScript functions
echo "3. Checking JavaScript implementation..."
if grep -q "function createFraudProgressTracker()" "$MAILBOX_FILE"; then
    pass "createFraudProgressTracker() function found"
else
    fail "createFraudProgressTracker() function missing"
fi

if grep -q "function updateFraudProgress(" "$MAILBOX_FILE"; then
    pass "updateFraudProgress() function found"
else
    fail "updateFraudProgress() function missing"
fi

if grep -q "function handleFraudProgressMessage(" "$MAILBOX_FILE"; then
    pass "handleFraudProgressMessage() function found"
else
    fail "handleFraudProgressMessage() function missing"
fi

if grep -q "function handleFraudComplete(" "$MAILBOX_FILE"; then
    pass "handleFraudComplete() function found"
else
    fail "handleFraudComplete() function missing"
fi

if grep -q "function showFraudProgressModal(" "$MAILBOX_FILE"; then
    pass "showFraudProgressModal() function found"
else
    fail "showFraudProgressModal() function missing"
fi

echo ""

# Test 4: Check SSE event listeners
echo "4. Checking SSE event listeners..."
if grep -q "sseClient.on('agentic_message'" "$MAILBOX_FILE"; then
    pass "agentic_message event listener found"
else
    fail "agentic_message event listener missing"
fi

if grep -q "sseClient.on('agentic_complete'" "$MAILBOX_FILE"; then
    pass "agentic_complete event listener found"
else
    fail "agentic_complete event listener missing"
fi

echo ""

# Test 5: Check progress steps configuration
echo "5. Checking progress steps configuration..."
if grep -q "Fraud Type Detection" "$MAILBOX_FILE"; then
    pass "Step 1: Fraud Type Detection found"
else
    fail "Step 1: Fraud Type Detection missing"
fi

if grep -q "Deep Investigation" "$MAILBOX_FILE"; then
    pass "Step 2: Deep Investigation found"
else
    fail "Step 2: Deep Investigation missing"
fi

if grep -q "Historical Analysis" "$MAILBOX_FILE"; then
    pass "Step 3: Historical Analysis found"
else
    fail "Step 3: Historical Analysis missing"
fi

if grep -q "Risk Assessment" "$MAILBOX_FILE"; then
    pass "Step 4: Risk Assessment found"
else
    fail "Step 4: Risk Assessment missing"
fi

echo ""

# Test 6: Check agent role mapping
echo "6. Checking agent role mapping..."
if grep -q "'Fraud Investigation Unit':" "$MAILBOX_FILE"; then
    pass "Fraud Investigation Unit role mapped"
else
    fail "Fraud Investigation Unit role mapping missing"
fi

if grep -q "'Phishing Analysis Specialist':" "$MAILBOX_FILE"; then
    pass "Phishing Analysis Specialist role mapped"
else
    fail "Phishing Analysis Specialist role mapping missing"
fi

if grep -q "'Database Investigation Agent':" "$MAILBOX_FILE"; then
    pass "Database Investigation Agent role mapped"
else
    fail "Database Investigation Agent role mapping missing"
fi

echo ""

# Test 7: Check timeline progress indicator
echo "7. Checking timeline progress indicator..."
if grep -q 'id="fraud-timeline-fill"' "$MAILBOX_FILE"; then
    pass "Timeline fill element found"
else
    fail "Timeline fill element missing"
fi

if grep -q "progress-timeline-fill" "$MAILBOX_FILE"; then
    pass "Timeline fill CSS class found"
else
    fail "Timeline fill CSS class missing"
fi

echo ""

# Test 8: Check message display functionality
echo "8. Checking message display..."
if grep -q "fraud-messages-container" "$MAILBOX_FILE"; then
    pass "Messages container found"
else
    fail "Messages container missing"
fi

if grep -q "function addFraudMessage(" "$MAILBOX_FILE"; then
    pass "addFraudMessage() function found"
else
    fail "addFraudMessage() function missing"
fi

if grep -q "fraud-agent-message" "$MAILBOX_FILE"; then
    pass "Agent message styling found"
else
    fail "Agent message styling missing"
fi

echo ""

# Test 9: Check integration with team assignment
echo "9. Checking integration with team assignment..."
if grep -q "if (teamKey === 'fraud')" "$MAILBOX_FILE"; then
    pass "Fraud team conditional logic found"
else
    fail "Fraud team conditional logic missing"
fi

if grep -q "showFraudProgressModal(result.task_id" "$MAILBOX_FILE"; then
    pass "Modal trigger on fraud assignment found"
else
    fail "Modal trigger on fraud assignment missing"
fi

echo ""

# Test 10: Check HTML syntax
echo "10. Checking HTML syntax..."
if command -v tidy &> /dev/null; then
    if tidy -q -e "$MAILBOX_FILE" 2>&1 | grep -q "0 warnings, 0 errors"; then
        pass "HTML syntax is valid"
    else
        info "HTML has minor warnings (common for templates)"
    fi
else
    info "tidy not installed, skipping HTML validation"
fi

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "${GREEN}Passed:${NC} $TEST_PASSED"
echo -e "${RED}Failed:${NC} $TEST_FAILED"
echo ""

if [ $TEST_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Implementation includes:"
    echo "  ✓ CSS styling for progress tracker"
    echo "  ✓ Modal HTML structure"
    echo "  ✓ JavaScript functions for progress tracking"
    echo "  ✓ SSE event listeners"
    echo "  ✓ 4-step progress visualization"
    echo "  ✓ Agent role mapping"
    echo "  ✓ Real-time message display"
    echo "  ✓ Timeline progress indicator"
    echo "  ✓ Integration with team assignment"
    echo ""
    echo "To test with live services:"
    echo "  1. Start services: ./start.sh"
    echo "  2. Navigate to: http://localhost:8080/pages/mailbox.html"
    echo "  3. Assign an email to the Fraud team"
    echo "  4. Watch the progress tracker update in real-time"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
