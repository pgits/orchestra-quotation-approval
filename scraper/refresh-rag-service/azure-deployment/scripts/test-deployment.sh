#!/bin/bash
# Test the deployed Copilot Knowledge Refresh Service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_INFO_FILE="$(dirname "$SCRIPT_DIR")/deployment-info.json"

print_status "=== Testing Copilot Knowledge Refresh Service ==="
echo ""

# Load deployment information
print_step "1. Loading Deployment Information"
if [ ! -f "$DEPLOYMENT_INFO_FILE" ]; then
    print_error "Deployment info file not found: $DEPLOYMENT_INFO_FILE"
    print_error "Please run deploy-infrastructure.sh first"
    exit 1
fi

# Parse deployment info
RESOURCE_GROUP=$(jq -r '.deployment.resource_group' "$DEPLOYMENT_INFO_FILE")
CONTAINER_REGISTRY_NAME=$(jq -r '.container_registry.name' "$DEPLOYMENT_INFO_FILE")
SHAREPOINT_SITE_URL=$(jq -r '.configuration.sharepoint_site_url' "$DEPLOYMENT_INFO_FILE")
AGENT_ID=$(jq -r '.configuration.agent_id' "$DEPLOYMENT_INFO_FILE")

print_status "Test Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  SharePoint Site: $SHAREPOINT_SITE_URL"
echo "  Agent ID: $AGENT_ID"
echo ""

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run tests
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing $test_name... "
    
    if eval "$test_command" &> /dev/null; then
        print_success "PASSED"
        ((TESTS_PASSED++))
        return 0
    else
        print_fail "FAILED"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test 1: Azure CLI Authentication
print_step "2. Testing Azure CLI Authentication"
run_test "Azure CLI authentication" "az account show"

# Test 2: Resource Group Exists
print_step "3. Testing Resource Group"
run_test "Resource group existence" "az group show --name '$RESOURCE_GROUP'"

# Test 3: Container Registry Exists
print_step "4. Testing Container Registry"
run_test "Container registry existence" "az acr show --name '$CONTAINER_REGISTRY_NAME'"

# Test 4: Container Instance Status
print_step "5. Testing Container Instance"
CONTAINER_INSTANCE_NAME="copilot-refresh-container"

if az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_INSTANCE_NAME" &> /dev/null; then
    print_success "Container instance exists"
    ((TESTS_PASSED++))
    
    # Check container state
    CONTAINER_STATE=$(az container show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CONTAINER_INSTANCE_NAME" \
        --query containers[0].instanceView.currentState.state -o tsv)
    
    if [ "$CONTAINER_STATE" = "Running" ]; then
        print_success "Container is running"
        ((TESTS_PASSED++))
    else
        print_fail "Container is not running (state: $CONTAINER_STATE)"
        ((TESTS_FAILED++))
    fi
else
    print_fail "Container instance not found"
    ((TESTS_FAILED++))
fi

# Test 5: Container Health Endpoint
print_step "6. Testing Container Health Endpoint"
CONTAINER_FQDN=$(az container show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_INSTANCE_NAME" \
    --query ipAddress.fqdn -o tsv 2>/dev/null)

if [ -n "$CONTAINER_FQDN" ] && [ "$CONTAINER_FQDN" != "null" ]; then
    print_status "Container FQDN: $CONTAINER_FQDN"
    
    # Test health endpoint
    HEALTH_URL="http://$CONTAINER_FQDN:8080/health"
    
    echo -n "Testing health endpoint... "
    if curl -s -f "$HEALTH_URL" > /dev/null 2>&1; then
        print_success "PASSED"
        ((TESTS_PASSED++))
        
        # Get health status
        HEALTH_STATUS=$(curl -s "$HEALTH_URL" | jq -r '.status' 2>/dev/null)
        if [ "$HEALTH_STATUS" = "healthy" ]; then
            print_success "Service is healthy"
            ((TESTS_PASSED++))
        else
            print_warning "Service health status: $HEALTH_STATUS"
            ((TESTS_FAILED++))
        fi
    else
        print_fail "FAILED"
        ((TESTS_FAILED++))
    fi
else
    print_warning "Container FQDN not available"
    ((TESTS_FAILED++))
fi

# Test 6: Managed Identity
print_step "7. Testing Managed Identity"
MANAGED_IDENTITY_NAME="copilot-refresh-identity"

if az identity show --resource-group "$RESOURCE_GROUP" --name "$MANAGED_IDENTITY_NAME" &> /dev/null; then
    print_success "Managed identity exists"
    ((TESTS_PASSED++))
    
    # Check role assignments
    MANAGED_IDENTITY_ID=$(az identity show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$MANAGED_IDENTITY_NAME" \
        --query principalId -o tsv)
    
    ROLE_ASSIGNMENTS=$(az role assignment list --assignee "$MANAGED_IDENTITY_ID" --query length(@))
    
    if [ "$ROLE_ASSIGNMENTS" -gt 0 ]; then
        print_success "Role assignments exist ($ROLE_ASSIGNMENTS found)"
        ((TESTS_PASSED++))
    else
        print_fail "No role assignments found"
        ((TESTS_FAILED++))
    fi
else
    print_fail "Managed identity not found"
    ((TESTS_FAILED++))
fi

# Test 7: Application Insights
print_step "8. Testing Application Insights"
APP_INSIGHTS_NAME="copilot-refresh-insights"

if az monitor app-insights component show --resource-group "$RESOURCE_GROUP" --app "$APP_INSIGHTS_NAME" &> /dev/null; then
    print_success "Application Insights exists"
    ((TESTS_PASSED++))
    
    # Check instrumentation key
    INSTRUMENTATION_KEY=$(az monitor app-insights component show \
        --resource-group "$RESOURCE_GROUP" \
        --app "$APP_INSIGHTS_NAME" \
        --query instrumentationKey -o tsv)
    
    if [ -n "$INSTRUMENTATION_KEY" ]; then
        print_success "Instrumentation key available"
        ((TESTS_PASSED++))
    else
        print_fail "Instrumentation key not found"
        ((TESTS_FAILED++))
    fi
else
    print_fail "Application Insights not found"
    ((TESTS_FAILED++))
fi

# Test 8: Container Logs
print_step "9. Testing Container Logs"
echo "Recent container logs:"
echo "----------------------------------------"
az container logs --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_INSTANCE_NAME" --tail 10 2>/dev/null || print_warning "Could not retrieve logs"
echo "----------------------------------------"

# Test 9: SharePoint Connectivity (if container is running)
if [ "$CONTAINER_STATE" = "Running" ] && [ -n "$CONTAINER_FQDN" ]; then
    print_step "10. Testing SharePoint Connectivity"
    
    # Check status endpoint for SharePoint connection info
    STATUS_URL="http://$CONTAINER_FQDN:8080/status"
    
    echo -n "Testing status endpoint... "
    if curl -s -f "$STATUS_URL" > /dev/null 2>&1; then
        print_success "PASSED"
        ((TESTS_PASSED++))
        
        # Display status info
        echo "Service Status:"
        curl -s "$STATUS_URL" | jq '.' 2>/dev/null || echo "Could not parse status JSON"
    else
        print_fail "FAILED"
        ((TESTS_FAILED++))
    fi
fi

# Test Summary
print_step "11. Test Summary"
echo ""
print_status "=== TEST RESULTS ==="
print_status "Tests Passed: $TESTS_PASSED"
print_status "Tests Failed: $TESTS_FAILED"
print_status "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    print_success "🎉 All tests passed! The deployment is working correctly."
    echo ""
    print_status "Next Steps:"
    print_status "1. Upload a test file to SharePoint:"
    print_status "   $SHAREPOINT_SITE_URL/EC%20Synnex%20Files"
    print_status "2. Monitor the container logs:"
    print_status "   az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_INSTANCE_NAME --follow"
    print_status "3. Check Copilot Studio knowledge base for the uploaded file"
    echo ""
    exit 0
else
    print_error "❌ Some tests failed. Please review the issues above."
    echo ""
    print_status "Common Solutions:"
    print_status "1. Ensure API permissions are granted in Azure Portal"
    print_status "2. Check container logs for detailed error messages"
    print_status "3. Verify SharePoint site URL is correct"
    print_status "4. Confirm managed identity has required permissions"
    echo ""
    exit 1
fi