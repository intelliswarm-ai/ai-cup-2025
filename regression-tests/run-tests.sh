#!/bin/bash

# Frontend Regression Test Runner
# Ensures both frontends are running and executes regression tests

set -e

echo "🔄 Frontend Regression Test Runner"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
  echo -e "${YELLOW}📦 Installing dependencies...${NC}"
  npm install
  echo -e "${GREEN}✅ Dependencies installed${NC}"
  echo ""
fi

# Check if Playwright browsers are installed
if [ ! -d "node_modules/@playwright/test" ]; then
  echo -e "${YELLOW}🌐 Installing Playwright browsers...${NC}"
  npx playwright install --with-deps chromium
  echo -e "${GREEN}✅ Browsers installed${NC}"
  echo ""
fi

# Check if vanilla frontend is running
echo -e "${YELLOW}🔍 Checking vanilla frontend (http://localhost:80)...${NC}"
if curl -s -f http://localhost:80 > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Vanilla frontend is running${NC}"
else
  echo -e "${RED}❌ Vanilla frontend is NOT running${NC}"
  echo "   Start it with: docker-compose up frontend"
  exit 1
fi

# Check if Angular frontend is running
echo -e "${YELLOW}🔍 Checking Angular frontend (http://localhost:4200)...${NC}"
if curl -s -f http://localhost:4200 > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Angular frontend is running${NC}"
else
  echo -e "${RED}❌ Angular frontend is NOT running${NC}"
  echo "   Start it with: cd frontend-angular && npm start"
  echo "   OR: docker-compose up frontend-angular"
  exit 1
fi

# Check if backend is running
echo -e "${YELLOW}🔍 Checking backend API (http://localhost:8000)...${NC}"
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Backend API is running${NC}"
else
  echo -e "${YELLOW}⚠️  Backend API may not be running${NC}"
  echo "   Tests may fail if backend is required"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run tests
echo -e "${YELLOW}🧪 Running regression tests...${NC}"
echo ""

npx playwright test "$@"

TEST_EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}✅ All tests passed!${NC}"
  echo ""
  echo "📊 View detailed report:"
  echo "   npm run test:report"
else
  echo -e "${RED}❌ Some tests failed${NC}"
  echo ""
  echo "📊 View detailed report:"
  echo "   npm run test:report"
  echo ""
  echo "🔍 Check screenshots:"
  echo "   test-results/screenshots/"
fi

echo ""

exit $TEST_EXIT_CODE
