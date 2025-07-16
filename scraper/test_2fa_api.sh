#!/bin/bash

# Test commands for 2FA Verification API

echo "2FA Verification API Test Commands"
echo "=================================="

# Base URL (API will try ports 5001, 5002, 5003, 5000 in order)
BASE_URL="http://localhost:5001"

echo ""
echo "1. Health Check:"
echo "curl -X GET $BASE_URL/health"
echo ""

echo "2. Start 2FA Listening:"
echo "curl -X POST $BASE_URL/2fa-start"
echo ""

echo "3. Check Status:"
echo "curl -X GET $BASE_URL/2fa-status"
echo ""

echo "4. Send Verification Code (MAIN ENDPOINT):"
echo "curl -X POST $BASE_URL/2fa-challenge \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"verificationId\": \"123456\"}'"
echo ""

echo "5. Stop 2FA Listening:"
echo "curl -X POST $BASE_URL/2fa-stop"
echo ""

echo "Test Scenarios:"
echo "==============="

echo ""
echo "Test 1: Complete Flow"
echo "# Start the API server first:"
echo "python3 run_verification_api.py"
echo ""
echo "# In another terminal:"
echo "curl -X POST $BASE_URL/2fa-start"
echo "curl -X POST $BASE_URL/2fa-challenge -H 'Content-Type: application/json' -d '{\"verificationId\": \"123456\"}'"
echo "curl -X GET $BASE_URL/2fa-status"
echo ""

echo "Test 2: Invalid Requests"
echo "# Missing verificationId:"
echo "curl -X POST $BASE_URL/2fa-challenge -H 'Content-Type: application/json' -d '{}'"
echo ""
echo "# Invalid JSON:"
echo "curl -X POST $BASE_URL/2fa-challenge -H 'Content-Type: application/json' -d 'invalid json'"
echo ""
echo "# Wrong content type:"
echo "curl -X POST $BASE_URL/2fa-challenge -d 'verificationId=123456'"
echo ""

echo "Test 3: Code not waiting"
echo "# Send code without starting listener:"
echo "curl -X POST $BASE_URL/2fa-challenge -H 'Content-Type: application/json' -d '{\"verificationId\": \"123456\"}'"
echo ""

echo "Production Usage:"
echo "================="
echo "# When scraper detects 2FA challenge:"
echo "# 1. Scraper automatically starts listening"
echo "# 2. User receives email with verification code"
echo "# 3. User runs this command with their code:"
echo "curl -X POST $BASE_URL/2fa-challenge -H 'Content-Type: application/json' -d '{\"verificationId\": \"YOUR_CODE_HERE\"}'"
echo ""
echo "NOTE: If port 5001 is in use, the API will try ports 5002, 5003, then 5000"
echo "Check the API startup logs to see which port is being used"