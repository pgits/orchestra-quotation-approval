#!/bin/bash
# TD SYNNEX Scraper + Knowledge Update Automation Script
# This script runs the local scraper, waits for email delivery, then runs the knowledge updater

set -e

# Configuration
EMAIL_SERVICE_URL="http://localhost:5001"
KNOWLEDGE_UPDATE_URL="https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io"
EMAIL_DELIVERY_WAIT=30  # seconds to wait for email delivery

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if email service is running
check_email_service() {
    print_status "Checking email verification service..."
    
    if curl -s "$EMAIL_SERVICE_URL/health" > /dev/null 2>&1; then
        print_success "Email verification service is running"
        return 0
    else
        print_error "Email verification service is not running on $EMAIL_SERVICE_URL"
        print_error "Please start the service with: ./email-verification-service/start_email_service.sh"
        return 1
    fi
}

# Function to get verification code
get_verification_code() {
    print_status "Getting latest TD SYNNEX verification code..."
    
    local code=$(curl -s "$EMAIL_SERVICE_URL/verification-code?sender=do_not_reply@tdsynnex.com&ignore_time_window=true" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['verification_code'])" 2>/dev/null)
    
    if [ -n "$code" ] && [ "$code" != "null" ]; then
        print_success "Found verification code: $code"
        echo "$code"
        return 0
    else
        print_error "No verification code found"
        return 1
    fi
}

# Function to run local scraper
run_local_scraper() {
    local verification_code=$1
    
    print_status "Running TD SYNNEX local scraper with verification code: $verification_code"
    echo "============================================================"
    
    if python3 production_scraper_with_2fa.py --verification-code "$verification_code"; then
        print_success "Local scraper completed successfully"
        return 0
    else
        print_error "Local scraper failed"
        return 1
    fi
}

# Function to wait for email delivery
wait_for_email_delivery() {
    print_status "Waiting $EMAIL_DELIVERY_WAIT seconds for TD SYNNEX email delivery..."
    
    for ((i=1; i<=EMAIL_DELIVERY_WAIT; i++)); do
        echo -n "."
        sleep 1
    done
    echo ""
    
    print_success "Email delivery wait completed"
}

# Function to run knowledge updater
run_knowledge_updater() {
    print_status "Running Azure knowledge updater..."
    
    local response=$(curl -s "$KNOWLEDGE_UPDATE_URL/latest-attachment?ignore_time_window=true&download=true&upload_sharepoint=true")
    
    if echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if data.get('success') else 1)" 2>/dev/null; then
        # Extract key information from response
        local filename=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['attachment_info']['filename'])" 2>/dev/null)
        local received_time=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['attachment_info']['received_time'])" 2>/dev/null)
        local file_size=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['attachment_info']['size'])" 2>/dev/null)
        
        print_success "Knowledge updater completed successfully!"
        print_success "Processed file: $filename"
        print_success "Email received: $received_time"
        print_success "File size: $file_size bytes"
        print_success "File uploaded to SharePoint and ready for Copilot Studio"
        
        return 0
    else
        print_error "Knowledge updater failed"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        return 1
    fi
}

# Function to show help
show_help() {
    echo "TD SYNNEX Scraper + Knowledge Update Automation Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo "  -w, --wait N  Set email delivery wait time in seconds (default: $EMAIL_DELIVERY_WAIT)"
    echo ""
    echo "This script performs the following steps:"
    echo "  1. Checks that email verification service is running"
    echo "  2. Gets the latest TD SYNNEX verification code"
    echo "  3. Runs the local scraper with the verification code"
    echo "  4. Waits for email delivery (default: $EMAIL_DELIVERY_WAIT seconds)"
    echo "  5. Runs the Azure knowledge updater to process the new attachment"
    echo ""
    echo "Prerequisites:"
    echo "  - Email verification service running on $EMAIL_SERVICE_URL"
    echo "  - Azure knowledge update service accessible at $KNOWLEDGE_UPDATE_URL"
    echo "  - Python3 installed"
    echo "  - TD SYNNEX scraper script (production_scraper_with_2fa.py)"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -w|--wait)
            EMAIL_DELIVERY_WAIT="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    echo -e "${BLUE}🚀 TD SYNNEX Scraper + Knowledge Update Automation${NC}"
    echo "============================================================"
    
    # Step 1: Check email service
    if ! check_email_service; then
        exit 1
    fi
    
    # Step 2: Get verification code
    verification_code=$(get_verification_code)
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # Step 3: Run local scraper
    if ! run_local_scraper "$verification_code"; then
        exit 1
    fi
    
    echo ""
    echo "============================================================"
    
    # Step 4: Wait for email delivery
    wait_for_email_delivery
    
    echo ""
    echo "============================================================"
    
    # Step 5: Run knowledge updater
    if ! run_knowledge_updater; then
        exit 1
    fi
    
    echo ""
    echo "============================================================"
    print_success "🎉 Complete workflow executed successfully!"
    print_success "TD SYNNEX data has been scraped and uploaded to SharePoint"
    print_success "Latest pricing information is now available for Copilot Studio"
    echo "============================================================"
}

# Run main function
main "$@"