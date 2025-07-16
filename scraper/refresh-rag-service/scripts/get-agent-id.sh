#!/bin/bash
# Get Copilot Studio Agent ID by name - macOS version
# This script helps you find the Agent ID for your Copilot Studio agent

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../config/config.json"

# Default values
AGENT_NAME=""
ENVIRONMENT_ID=""

# Function to show usage
show_usage() {
    cat <<EOF
Usage: $0 -AgentName "Agent Name" [-EnvironmentId "Environment ID"]

Options:
    -AgentName     Name of the Copilot Studio agent to find
    -EnvironmentId Optional environment ID to search in
    -h, --help     Show this help message

Examples:
    $0 -AgentName "Nathan's Hardware Buddy v.1"
    $0 -AgentName "My Agent" -EnvironmentId "12345678-1234-1234-1234-123456789012"
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
    if [ -n "$ENVIRONMENT_ID" ]; then
        log "Setting target environment: $ENVIRONMENT_ID"
        pac org select --environment "$ENVIRONMENT_ID"
    fi
}

# Function to find agent
find_agent() {
    log "Searching for Copilot Studio agent: $AGENT_NAME"
    
    # List all copilots in the environment
    local copilot_list=$(pac copilot list --json 2>/dev/null || echo "[]")
    
    if [ "$copilot_list" = "[]" ] || [ -z "$copilot_list" ]; then
        log "WARNING: No copilots found in the current environment."
        return 1
    fi
    
    # Find the agent by name using jq
    local target_agent=$(echo "$copilot_list" | jq -r --arg name "$AGENT_NAME" '.[] | select(.DisplayName == $name or .Name == $name)')
    
    if [ -n "$target_agent" ] && [ "$target_agent" != "null" ]; then
        # Extract agent details
        local display_name=$(echo "$target_agent" | jq -r '.DisplayName')
        local schema_name=$(echo "$target_agent" | jq -r '.Name')
        local agent_id=$(echo "$target_agent" | jq -r '.Id')
        local environment_id=$(echo "$target_agent" | jq -r '.EnvironmentId')
        local state=$(echo "$target_agent" | jq -r '.State')
        local created_on=$(echo "$target_agent" | jq -r '.CreatedOn')
        local modified_on=$(echo "$target_agent" | jq -r '.ModifiedOn')
        
        echo ""
        log "=== AGENT FOUND ==="
        echo "Display Name: $display_name"
        echo "Schema Name: $schema_name"
        echo "Agent ID: $agent_id"
        echo "Environment: $environment_id"
        echo "State: $state"
        echo "Created: $created_on"
        echo "Modified: $modified_on"
        echo ""
        log "=== NEXT STEPS ==="
        echo "1. Copy the Agent ID: $agent_id"
        echo "2. Update config.json with this ID"
        echo "3. Run the deploy-flow.sh script"
        echo ""
        
        # Update config.json if it exists
        if [ -f "$CONFIG_FILE" ]; then
            log "Updating config.json with Agent ID..."
            
            # Create a temporary file with updated config
            local temp_config=$(mktemp)
            jq --arg agent_id "$agent_id" --arg env_id "$environment_id" \
                '.copilotStudio.agentId = $agent_id | .copilotStudio.environment.id = $env_id' \
                "$CONFIG_FILE" > "$temp_config"
            
            # Replace the original config file
            mv "$temp_config" "$CONFIG_FILE"
            
            log "Config.json updated with Agent ID: $agent_id"
        else
            log "WARNING: Config.json not found at: $CONFIG_FILE"
        fi
        
        return 0
    else
        log "WARNING: Agent '$AGENT_NAME' not found in the current environment."
        
        # Show available agents
        log "Available agents:"
        echo "$copilot_list" | jq -r '.[] | "\(.DisplayName) (\(.Name)) - \(.Id)"' | while read -r line; do
            echo "  $line"
        done
        
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -AgentName)
            AGENT_NAME="$2"
            shift 2
            ;;
        -EnvironmentId)
            ENVIRONMENT_ID="$2"
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
if [ -z "$AGENT_NAME" ]; then
    log "ERROR: Agent name is required"
    show_usage
    exit 1
fi

# Main execution
main() {
    log "Starting agent search for: $AGENT_NAME"
    
    check_prerequisites
    check_authentication
    set_environment
    
    if find_agent; then
        log "Agent search completed successfully"
        exit 0
    else
        log "Agent search failed"
        exit 1
    fi
}

# Run main function
main "$@"