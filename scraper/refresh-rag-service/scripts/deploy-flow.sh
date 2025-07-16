#!/bin/bash
# Deploy Copilot Knowledge Refresh Flow to Power Automate - macOS version
# Prerequisites: Install Power Platform CLI and authenticate

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLOW_FILE="${SCRIPT_DIR}/../flows/copilot-knowledge-refresh-flow.json"
CONFIG_FILE="${SCRIPT_DIR}/../config/config.json"

# Default values
ENVIRONMENT_ID=""
SUBSCRIPTION_ID=""
RESOURCE_GROUP_NAME=""
FLOW_NAME="Copilot-Knowledge-Refresh-Flow"

# Function to show usage
show_usage() {
    cat <<EOF
Usage: $0 -EnvironmentId "ENV_ID" -SubscriptionId "SUB_ID" -ResourceGroupName "RG_NAME" [-FlowName "FLOW_NAME"]

Options:
    -EnvironmentId      Power Platform environment ID
    -SubscriptionId     Azure subscription ID
    -ResourceGroupName  Azure resource group name
    -FlowName          Name for the flow (optional, default: Copilot-Knowledge-Refresh-Flow)
    -h, --help         Show this help message

Examples:
    $0 -EnvironmentId "12345678-1234-1234-1234-123456789012" -SubscriptionId "87654321-4321-4321-4321-210987654321" -ResourceGroupName "myResourceGroup"
EOF
}

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check prerequisites
check_prerequisites() {
    # Check if Power Platform CLI is installed
    if ! command -v pac &> /dev/null; then
        log "ERROR: Power Platform CLI is not installed."
        log "Please run: ./setup-macos.sh first"
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log "ERROR: jq is not installed."
        log "Please run: brew install jq"
        exit 1
    fi
    
    # Check if flow file exists
    if [ ! -f "$FLOW_FILE" ]; then
        log "ERROR: Flow definition file not found at: $FLOW_FILE"
        exit 1
    fi
}

# Function to check authentication
check_authentication() {
    log "Checking Power Platform CLI authentication..."
    
    local auth_list=$(pac auth list 2>/dev/null || echo "")
    
    if [[ ! "$auth_list" =~ "Active" ]]; then
        log "ERROR: Not authenticated to Power Platform."
        log "Please run: pac auth create --tenant YOUR_TENANT_ID"
        exit 1
    fi
    
    log "Authentication verified."
}

# Function to set environment
set_environment() {
    log "Setting target environment: $ENVIRONMENT_ID"
    pac org select --environment "$ENVIRONMENT_ID"
}

# Function to update flow definition
update_flow_definition() {
    log "Updating flow definition with connection references..."
    
    # Create updated flow file
    local updated_flow_file="${SCRIPT_DIR}/../flows/copilot-knowledge-refresh-flow-updated.json"
    
    # Read and update the flow definition
    jq --arg sub_id "$SUBSCRIPTION_ID" --arg rg_name "$RESOURCE_GROUP_NAME" \
        '.parameters."$connections".value.shared_commondataservice.connectionId = "/subscriptions/\($sub_id)/resourceGroups/\($rg_name)/providers/Microsoft.Web/connections/shared_commondataservice" |
         .parameters."$connections".value.shared_onedriveforbusiness.connectionId = "/subscriptions/\($sub_id)/resourceGroups/\($rg_name)/providers/Microsoft.Web/connections/shared_onedriveforbusiness"' \
        "$FLOW_FILE" > "$updated_flow_file"
    
    log "Flow definition updated and saved to: $updated_flow_file"
    echo "$updated_flow_file"
}

# Function to show deployment instructions
show_deployment_instructions() {
    local updated_flow_file=$1
    
    log "Flow definition preparation completed!"
    echo ""
    echo "=============================================="
    echo "       MANUAL DEPLOYMENT STEPS"
    echo "=============================================="
    echo ""
    echo "1. Open Power Automate portal:"
    echo "   https://powerautomate.microsoft.com"
    echo ""
    echo "2. Navigate to your environment:"
    echo "   Environment ID: $ENVIRONMENT_ID"
    echo ""
    echo "3. Import the flow:"
    echo "   - Click 'My flows' > 'Import' > 'Import Package (Legacy)'"
    echo "   - Upload file: $updated_flow_file"
    echo ""
    echo "4. Configure connections:"
    echo "   - Dataverse: Connect to your Dataverse environment"
    echo "   - OneDrive for Business: Connect to your OneDrive account"
    echo ""
    echo "5. Set flow parameters:"
    echo "   - CopilotStudioAgentId: (Get from get-agent-id.sh)"
    echo ""
    echo "6. Save and test the flow"
    echo ""
    echo "7. Get the trigger URL:"
    echo "   - Open the flow > Click 'Request' trigger"
    echo "   - Copy the 'HTTP POST URL'"
    echo "   - Update config.json with this URL"
    echo ""
    echo "=============================================="
    echo "       GETTING AGENT ID"
    echo "=============================================="
    echo ""
    echo "Run this command to get your agent ID:"
    echo "  ./get-agent-id.sh -AgentName \"Nathan's Hardware Buddy v.1\""
    echo ""
    echo "=============================================="
    echo "       TESTING THE FLOW"
    echo "=============================================="
    echo ""
    echo "After deployment, test with:"
    echo "  ./upload-file.sh ~/Downloads/ec-synnex-701601-0708-0927.xls"
    echo ""
}

# Function to update config file
update_config() {
    if [ -f "$CONFIG_FILE" ]; then
        log "Updating config.json with deployment information..."
        
        # Create a temporary file with updated config
        local temp_config=$(mktemp)
        jq --arg sub_id "$SUBSCRIPTION_ID" --arg rg_name "$RESOURCE_GROUP_NAME" \
            '.powerAutomate.subscriptionId = $sub_id | .powerAutomate.resourceGroup = $rg_name' \
            "$CONFIG_FILE" > "$temp_config"
        
        # Replace the original config file
        mv "$temp_config" "$CONFIG_FILE"
        
        log "Config.json updated with deployment information"
    else
        log "WARNING: Config.json not found at: $CONFIG_FILE"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -EnvironmentId)
            ENVIRONMENT_ID="$2"
            shift 2
            ;;
        -SubscriptionId)
            SUBSCRIPTION_ID="$2"
            shift 2
            ;;
        -ResourceGroupName)
            RESOURCE_GROUP_NAME="$2"
            shift 2
            ;;
        -FlowName)
            FLOW_NAME="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log "ERROR: Unknown argument: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$ENVIRONMENT_ID" ] || [ -z "$SUBSCRIPTION_ID" ] || [ -z "$RESOURCE_GROUP_NAME" ]; then
    log "ERROR: Missing required parameters"
    show_usage
    exit 1
fi

# Main execution
main() {
    log "Starting Power Automate flow deployment preparation..."
    
    check_prerequisites
    check_authentication
    set_environment
    
    local updated_flow_file=$(update_flow_definition)
    
    update_config
    
    show_deployment_instructions "$updated_flow_file"
    
    log "Deployment preparation completed successfully!"
}

# Run main function
main "$@"