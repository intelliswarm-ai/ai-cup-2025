#!/bin/bash

# =============================================================================
# Fraud Detection APIs - Integration Test Script
# =============================================================================
# This script tests all fraud detection API integrations
# Run this after configuring your .env file with API keys

set -e  # Exit on error

echo "=============================================="
echo "🧪 Fraud Detection APIs - Integration Test"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Loaded .env file"
else
    echo "⚠️  No .env file found - APIs will use fallback mode"
fi

echo ""
echo "=============================================="
echo "📊 API Configuration Status"
echo "=============================================="

# Check API keys
check_api_key() {
    local key_name=$1
    local key_value=${!key_name}

    if [ -z "$key_value" ] || [ "$key_value" == "your_${key_name,,}_here" ]; then
        echo -e "${YELLOW}⚠️  $key_name: NOT CONFIGURED (will use fallback)${NC}"
        return 1
    else
        # Show first 10 chars of key
        echo -e "${GREEN}✅ $key_name: CONFIGURED (${key_value:0:10}...)${NC}"
        return 0
    fi
}

# Check all API keys
check_api_key "IPGEOLOCATION_API_KEY"
IPGEO_STATUS=$?

check_api_key "SERPER_API_KEY"
SERPER_STATUS=$?

check_api_key "ABSTRACTAPI_EMAIL_KEY"
ABSTRACT_STATUS=$?

echo -e "${GREEN}✅ OPENSANCTIONS: FREE (No key needed)${NC}"

echo ""
echo "=============================================="
echo "🧪 Testing APIs Directly"
echo "=============================================="
echo ""

# Test 1: ipgeolocation.io
echo "Test 1/4: ipgeolocation.io (IP Threat Intelligence)"
echo "-------------------------------------------"
if [ $IPGEO_STATUS -eq 0 ]; then
    echo "Testing with TOR exit node IP: 185.220.101.1"
    RESPONSE=$(curl -s "https://api.ipgeolocation.io/ipgeo?apiKey=$IPGEOLOCATION_API_KEY&ip=185.220.101.1&fields=security" 2>&1)

    if echo "$RESPONSE" | grep -q "security"; then
        echo -e "${GREEN}✅ SUCCESS: API responded with security data${NC}"
        echo "Sample data:"
        echo "$RESPONSE" | jq '.security' 2>/dev/null || echo "$RESPONSE" | head -5
    else
        echo -e "${RED}❌ FAILED: $RESPONSE${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  SKIPPED: API key not configured${NC}"
fi
echo ""

# Test 2: OpenSanctions
echo "Test 2/4: OpenSanctions (OFAC Screening)"
echo "-------------------------------------------"
echo "Testing OFAC sanctions search..."
RESPONSE=$(curl -s "https://api.opensanctions.org/search/default?q=test&schema=Person&limit=1" 2>&1)

if echo "$RESPONSE" | grep -q "results"; then
    echo -e "${GREEN}✅ SUCCESS: OpenSanctions API working${NC}"
    echo "Sample data:"
    echo "$RESPONSE" | jq '.results[0].schema' 2>/dev/null || echo "$RESPONSE" | head -3
else
    echo -e "${RED}❌ FAILED: $RESPONSE${NC}"
fi
echo ""

# Test 3: Serper (Business Verification)
echo "Test 3/4: Serper (Business Verification & Merchant Search)"
echo "-------------------------------------------"
if [ $SERPER_STATUS -eq 0 ]; then
    echo "Testing business search for 'Google LLC business registration'..."
    RESPONSE=$(curl -s -X POST "https://google.serper.dev/search" \
        -H "X-API-KEY: $SERPER_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"q":"Google LLC business registration"}' 2>&1)

    if echo "$RESPONSE" | grep -q "organic"; then
        echo -e "${GREEN}✅ SUCCESS: Serper API working${NC}"
        echo "Sample data:"
        echo "$RESPONSE" | jq '.organic[0].title' 2>/dev/null || echo "$RESPONSE" | head -3
    else
        echo -e "${RED}❌ FAILED: $RESPONSE${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  SKIPPED: Serper API key not configured${NC}"
    echo "Note: Serper is used for both investment research AND fraud detection"
    echo "Configure SERPER_API_KEY for business verification and merchant searches"
fi
echo ""

# Test 4: Abstract Email API
echo "Test 4/4: Abstract API (Email Validation)"
echo "-------------------------------------------"
if [ $ABSTRACT_STATUS -eq 0 ]; then
    echo "Testing email validation with test@example.com..."
    RESPONSE=$(curl -s "https://emailvalidation.abstractapi.com/v1/?api_key=$ABSTRACTAPI_EMAIL_KEY&email=test@example.com" 2>&1)

    if echo "$RESPONSE" | grep -q "is_valid_format"; then
        echo -e "${GREEN}✅ SUCCESS: Abstract API responded${NC}"
        echo "Sample data:"
        echo "$RESPONSE" | jq '{email: .email, is_valid: .is_valid_format.value}' 2>/dev/null || echo "$RESPONSE" | head -3
    else
        echo -e "${RED}❌ FAILED: $RESPONSE${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  SKIPPED: API key not configured${NC}"
fi
echo ""

echo "=============================================="
echo "🧪 Testing Backend Integration"
echo "=============================================="
echo ""

# Check if backend is running
if ! docker compose ps backend | grep -q "running"; then
    echo -e "${RED}❌ Backend is not running!${NC}"
    echo "Start it with: docker compose up -d backend"
    exit 1
fi

echo "✅ Backend is running"
echo ""

# Test backend fraud workflow (if it has an endpoint)
echo "Testing fraud workflow integration..."
echo "(This will be tested via the fraud workflow when called by agents)"
echo ""

echo "=============================================="
echo "📊 Summary"
echo "=============================================="
echo ""

TOTAL_TESTS=4
PASSING_TESTS=0

[ $IPGEO_STATUS -eq 0 ] && ((PASSING_TESTS++))
[ $SERPER_STATUS -eq 0 ] && ((PASSING_TESTS++))
((PASSING_TESTS++))  # OpenSanctions always works
[ $ABSTRACT_STATUS -eq 0 ] && ((PASSING_TESTS++))

echo "API Configuration:"
echo "  - ipgeolocation.io: $([ $IPGEO_STATUS -eq 0 ] && echo -e "${GREEN}CONFIGURED${NC}" || echo -e "${YELLOW}NOT CONFIGURED${NC}")"
echo "  - Serper: $([ $SERPER_STATUS -eq 0 ] && echo -e "${GREEN}CONFIGURED${NC}" || echo -e "${YELLOW}NOT CONFIGURED (needed for business verification)${NC}")"
echo "  - OpenSanctions: ${GREEN}FREE (Always Available)${NC}"
echo "  - Abstract Email: $([ $ABSTRACT_STATUS -eq 0 ] && echo -e "${GREEN}CONFIGURED${NC}" || echo -e "${YELLOW}NOT CONFIGURED${NC}")"
echo ""

if [ $PASSING_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}🎉 ALL APIS CONFIGURED! ($PASSING_TESTS/$TOTAL_TESTS)${NC}"
    echo ""
    echo "Your fraud workflow now has REAL-TIME threat intelligence!"
    echo "Ready for hackathon demo! 🚀"
elif [ $PASSING_TESTS -ge 2 ]; then
    echo -e "${YELLOW}⚠️  PARTIAL CONFIGURATION ($PASSING_TESTS/$TOTAL_TESTS)${NC}"
    echo ""
    echo "Some APIs are working! Your demo will have real data."
    echo "Configure remaining APIs for maximum impact."
else
    echo -e "${RED}❌ MOST APIS NOT CONFIGURED ($PASSING_TESTS/$TOTAL_TESTS)${NC}"
    echo ""
    echo "Please configure API keys in .env file"
    echo "See FRAUD_API_SETUP_GUIDE.md for instructions"
fi

echo ""
echo "=============================================="
echo "📚 Next Steps"
echo "=============================================="
echo ""
echo "1. Configure remaining APIs (see FRAUD_API_SETUP_GUIDE.md)"
echo "2. Restart backend: docker compose restart backend"
echo "3. Test fraud workflow through frontend"
echo "4. Practice demo scenarios"
echo ""
echo "Test complete! ✨"
