#!/bin/bash

# Test Content-Aware Fraud Detection - Phishing Email Example

echo "========================================"
echo "Content-Aware Fraud Detection Test"
echo "Testing PHISHING email scenario"
echo "========================================"
echo ""

PHISHING_QUERY="URGENT: Your account has been compromised.

From: security@paypa1-security.com
Subject: Immediate Action Required - Account Suspended

Dear valued customer,

We have detected suspicious activity on your PayPal account. Your account has been temporarily suspended for your protection.

To restore access, please verify your identity immediately by clicking the link below:
http://paypa1-verify.tk/login?ref=12345

You must complete verification within 24 hours or your account will be permanently closed.

Security Team
PayPal (Not affiliated with PayPal Inc.)"

echo "Submitting phishing email analysis request..."
curl -s -X POST http://localhost:8000/api/agentic/direct-query \
  -H "Content-Type: application/json" \
  -d "{\"team\": \"fraud\", \"query\": $(echo "$PHISHING_QUERY" | python3 -c 'import sys, json; print(json.dumps(sys.stdin.read()))')}" | python3 -m json.tool

echo ""
echo "✅ Test submitted! Check UI at:"
echo "   http://localhost:8080/pages/agentic-teams.html?team=fraud"
