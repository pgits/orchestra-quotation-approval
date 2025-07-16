#!/bin/bash
# Copilot Studio Knowledge Base File Upload Script for macOS
# Automates the upload of ec-synnex files to the Copilot Studio agent

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../config/config.json"
LOG_FILE="${SCRIPT_DIR}/../logs/upload.log"

# Create logs directory if it doesn't exist
mkdir -p "${SCRIPT_DIR}/../logs"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to read JSON config
read_config() {
    local key=$1
    python3 -c "
import json
import sys
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    keys = '$key'.split('.')
    value = config
    for k in keys:
        value = value.get(k, {})
    print(value if value != {} else '')
except Exception as e:
    print('', file=sys.stderr)
    exit(1)
"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        log "ERROR: Python 3 is not installed. Please install Python 3."
        exit 1
    fi
    
    # Check if curl is installed
    if ! command -v curl &> /dev/null; then
        log "ERROR: curl is not installed. Please install curl."
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log "WARNING: jq is not installed. Installing via Homebrew..."
        if command -v brew &> /dev/null; then
            brew install jq
        else
            log "ERROR: Homebrew is not installed. Please install jq manually."
            exit 1
        fi
    fi
    
    # Check if config file exists
    if [ ! -f "$CONFIG_FILE" ]; then
        log "ERROR: Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
    
    log "Prerequisites check completed."
}

# Function to validate file
validate_file() {
    local file_path=$1
    
    log "Validating file: $file_path"
    
    # Check if file exists
    if [ ! -f "$file_path" ]; then
        log "ERROR: File not found: $file_path"
        exit 1
    fi
    
    # Check file extension
    local file_ext="${file_path##*.}"
    local supported_extensions=$(read_config "fileSettings.supportedExtensions")
    
    if [[ ! "$supported_extensions" =~ ".$file_ext" ]]; then
        log "ERROR: Unsupported file extension: .$file_ext"
        exit 1
    fi
    
    # Check file size
    local file_size=$(stat -f%z "$file_path")
    local max_size=$(read_config "fileSettings.maxFileSize")
    
    if [ "$file_size" -gt "$max_size" ]; then
        log "ERROR: File size ($file_size bytes) exceeds maximum ($max_size bytes)"
        exit 1
    fi
    
    log "File validation completed. Size: $file_size bytes"
}

# Function to upload file to OneDrive (placeholder)
upload_to_onedrive() {
    local file_path=$1
    local filename=$(basename "$file_path")
    
    log "Preparing file for OneDrive upload: $filename"
    
    # For now, we'll simulate the OneDrive upload
    # In a real implementation, you would use Microsoft Graph API
    local onedrive_path="/Knowledge_Base_Files/$filename"
    
    log "File prepared for OneDrive path: $onedrive_path"
    echo "$onedrive_path"
}

# Function to trigger Power Automate flow
trigger_power_automate_flow() {
    local onedrive_path=$1
    local filename=$2
    
    local trigger_url=$(read_config "powerAutomate.triggerUrl")
    
    if [ -z "$trigger_url" ]; then
        log "ERROR: Power Automate trigger URL not configured"
        exit 1
    fi
    
    log "Triggering Power Automate flow for file: $filename"
    
    # Create JSON payload
    local payload=$(cat <<EOF
{
    "FilePath": "$onedrive_path",
    "FileName": "$filename"
}
EOF
)
    
    # Send HTTP request to trigger flow
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$trigger_url")
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log "Power Automate flow triggered successfully"
        log "Response: $response"
        echo "$response"
    else
        log "ERROR: Failed to trigger Power Automate flow"
        exit 1
    fi
}

# Function to create audit log
create_audit_log() {
    local action=$1
    local details=$2
    
    local enable_audit=$(read_config "logging.enableAuditTrail")
    
    if [ "$enable_audit" != "true" ]; then
        return
    fi
    
    local agent_id=$(read_config "copilotStudio.agentId")
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    local log_entry=$(cat <<EOF
{
    "timestamp": "$timestamp",
    "action": "$action",
    "details": "$details",
    "agent_id": "$agent_id"
}
EOF
)
    
    echo "$log_entry" >> "${SCRIPT_DIR}/../logs/audit.jsonl"
}

# Main upload function
upload_file() {
    local file_path=$1
    
    if [ -z "$file_path" ]; then
        file_path=$(read_config "fileSettings.localFilePath")
        file_path="${file_path/#\~/$HOME}"  # Expand tilde
    fi
    
    log "Starting upload process for: $file_path"
    
    # Validate file
    validate_file "$file_path"
    
    # Upload to OneDrive
    local onedrive_path=$(upload_to_onedrive "$file_path")
    local filename=$(basename "$file_path")
    
    # Trigger Power Automate flow
    local result=$(trigger_power_automate_flow "$onedrive_path" "$filename")
    
    # Create audit log
    create_audit_log "file_upload" "File: $filename, Path: $onedrive_path"
    
    log "Upload process completed successfully"
    echo "Upload completed successfully!"
    echo "Result: $result"
}

# Function to show usage
show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS] [FILE_PATH]

Options:
    -h, --help          Show this help message
    -c, --config FILE   Specify configuration file (default: config/config.json)
    -v, --verbose       Enable verbose logging

Examples:
    $0                                          # Upload default file from config
    $0 ~/Downloads/ec-synnex-701601-0708-0927.xls  # Upload specific file
    $0 -c custom-config.json myfile.xls         # Use custom config
EOF
}

# Parse command line arguments
VERBOSE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -*)
            log "ERROR: Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            FILE_PATH="$1"
            shift
            ;;
    esac
done

# Main execution
main() {
    log "=== Copilot Studio Knowledge Base Upload Started ==="
    
    check_prerequisites
    upload_file "$FILE_PATH"
    
    log "=== Upload Process Completed ==="
}

# Run main function
main "$@"