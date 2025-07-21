#!/bin/bash

# TD SYNNEX Automated Scraping System Startup Script
# This script starts both the email verification service and triggers the Azure container scraper
# in the proper order to account for email delivery delays ("snail mail" timing)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
EMAIL_SERVICE_DIR="./email-verification-service"
AZURE_CONTAINER_URL="http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-challenge"
EMAIL_CHECK_DELAY=30  # seconds to wait between email checks
MAX_RETRIES=5         # maximum number of email check attempts

echo -e "${BLUE}🚀 TD SYNNEX Automated Scraping System${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# Step 1: Start Email Verification Service
echo -e "${BLUE}📧 Step 1: Starting Email Verification Service...${NC}"
if [ ! -f "$EMAIL_SERVICE_DIR/start_email_service.sh" ]; then
    echo -e "${RED}❌ Email service startup script not found at $EMAIL_SERVICE_DIR/start_email_service.sh${NC}"
    exit 1
fi

cd "$EMAIL_SERVICE_DIR"
echo -e "${YELLOW}⏳ Starting email verification service (this may take a moment)...${NC}"
./start_email_service.sh &
EMAIL_SERVICE_PID=$!
cd ..

# Wait for email service to be ready
echo -e "${YELLOW}⏳ Waiting for email service to initialize...${NC}"
sleep 10

# Check if email service is responding
for i in {1..10}; do
    if curl -s "http://localhost:5001/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Email verification service is ready${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ Email service failed to start after 30 seconds${NC}"
        kill $EMAIL_SERVICE_PID 2>/dev/null || true
        exit 1
    fi
    sleep 3
done

# Step 2: Check Azure Container Status
echo ""
echo -e "${BLUE}🏗️ Step 2: Checking Azure Container Status...${NC}"
if ! curl -s "${AZURE_CONTAINER_URL%/2fa-challenge}/2fa-status" > /dev/null 2>&1; then
    echo -e "${RED}❌ Azure container is not responding${NC}"
    echo -e "${YELLOW}   Please ensure the container is deployed and running${NC}"
    echo -e "${YELLOW}   Container URL: ${AZURE_CONTAINER_URL%/2fa-challenge}${NC}"
    kill $EMAIL_SERVICE_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Azure container is responsive${NC}"

# Step 3: Wait for and Process Verification Codes
echo ""
echo -e "${BLUE}🔄 Step 3: Monitoring for TD SYNNEX 2FA Verification Codes...${NC}"
echo -e "${YELLOW}💡 The system will now:${NC}"
echo -e "${YELLOW}   1. Monitor your email for TD SYNNEX 2FA codes${NC}"
echo -e "${YELLOW}   2. Automatically submit codes to the Azure container${NC}"
echo -e "${YELLOW}   3. Trigger the scraper to complete the download process${NC}"
echo -e "${YELLOW}   4. Account for 'snail mail' delays in email delivery${NC}"
echo ""

# Function to check for and submit verification codes
submit_verification_code() {
    local attempt=$1
    echo -e "${BLUE}🔍 Attempt $attempt: Checking for verification codes...${NC}"
    
    local response=$(curl -s "http://localhost:5001/verification-code?sender=do_not_reply@tdsynnex.com&ignore_time_window=true&automatic_submit=true&target_url=$AZURE_CONTAINER_URL" || echo '{"success": false}')
    
    if echo "$response" | jq -e '.success and .post_result.success' > /dev/null 2>&1; then
        local verification_code=$(echo "$response" | jq -r '.verification_code')
        local post_status=$(echo "$response" | jq -r '.post_result.status_code')
        
        echo -e "${GREEN}✅ Found and submitted verification code: $verification_code${NC}"
        echo -e "${GREEN}✅ Azure container response: HTTP $post_status${NC}"
        echo -e "${GREEN}🎉 Scraper session initiated successfully!${NC}"
        echo ""
        echo -e "${BLUE}📬 What happens next:${NC}"
        echo -e "${YELLOW}   • The Azure container is now running the TD SYNNEX scraper${NC}"
        echo -e "${YELLOW}   • It will log in, apply Microsoft filters, and trigger download${NC}"
        echo -e "${YELLOW}   • TD SYNNEX will EMAIL you the price/availability attachment${NC}"
        echo -e "${YELLOW}   • Check your email for the attachment file${NC}"
        return 0
    elif echo "$response" | jq -e '.success' > /dev/null 2>&1; then
        echo -e "${YELLOW}⏳ Email verification service is working, but no new codes found${NC}"
        return 1
    else
        echo -e "${RED}❌ Email verification service error${NC}"
        return 1
    fi
}

# Main monitoring loop with snail mail delay accommodation
echo -e "${YELLOW}⏳ Starting monitoring loop (accounting for email delivery delays)...${NC}"

for attempt in $(seq 1 $MAX_RETRIES); do
    if submit_verification_code $attempt; then
        # Success! Code found and submitted
        break
    fi
    
    if [ $attempt -lt $MAX_RETRIES ]; then
        echo -e "${YELLOW}   Waiting $EMAIL_CHECK_DELAY seconds for potential email delays...${NC}"
        sleep $EMAIL_CHECK_DELAY
    fi
done

if [ $attempt -eq $MAX_RETRIES ]; then
    echo ""
    echo -e "${YELLOW}⚠️ No new verification codes found after $MAX_RETRIES attempts${NC}"
    echo -e "${YELLOW}💡 This could mean:${NC}"
    echo -e "${YELLOW}   • No recent TD SYNNEX 2FA activity${NC}"
    echo -e "${YELLOW}   • Email delivery delays (try running again in a few minutes)${NC}"
    echo -e "${YELLOW}   • All recent codes have already been processed${NC}"
fi

# Final status
echo ""
echo -e "${BLUE}📊 Final Status:${NC}"
echo -e "${GREEN}✅ Email verification service: Running (PID: $EMAIL_SERVICE_PID)${NC}"
echo -e "${GREEN}✅ Azure container: Ready for verification codes${NC}"
echo -e "${BLUE}🔗 Container endpoint: $AZURE_CONTAINER_URL${NC}"

echo ""
echo -e "${BLUE}🛠️ Manual Controls:${NC}"
echo -e "${YELLOW}   Stop email service: kill $EMAIL_SERVICE_PID${NC}"
echo -e "${YELLOW}   Check email service: curl http://localhost:5001/health${NC}"
echo -e "${YELLOW}   Check container: curl ${AZURE_CONTAINER_URL%/2fa-challenge}/2fa-status${NC}"

echo ""
echo -e "${GREEN}🎯 TD SYNNEX Automation System is now monitoring and ready!${NC}"
echo -e "${BLUE}=======================================${NC}"