#!/bin/bash
# Web-based setup for Copilot Studio Knowledge Base Refresh
# This approach bypasses CLI installation issues and uses web interfaces

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

print_status "=== Web-Based Setup for Copilot Studio Knowledge Refresh ==="
echo ""
print_status "Since CLI installation is having issues, we'll use web interfaces instead."
echo ""

# Check if we have the necessary files
if [ ! -f "$BASE_DIR/flows/copilot-knowledge-refresh-flow.json" ]; then
    print_error "Flow definition file not found!"
    exit 1
fi

# Create a simplified upload script that doesn't require pac CLI
print_status "Creating simplified upload script..."

cat > "$BASE_DIR/scripts/simple-upload.sh" << 'EOF'
#!/bin/bash
# Simplified upload script that works without Power Platform CLI
# Uses HTTP requests directly to trigger the Power Automate flow

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config/config.json"

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

# Main upload function
upload_file() {
    local file_path=${1:-$(read_config "fileSettings.localFilePath")}
    file_path="${file_path/#\~/$HOME}"  # Expand tilde
    
    if [ ! -f "$file_path" ]; then
        echo "ERROR: File not found: $file_path"
        exit 1
    fi
    
    local trigger_url=$(read_config "powerAutomate.triggerUrl")
    if [ -z "$trigger_url" ]; then
        echo "ERROR: Power Automate trigger URL not configured in config.json"
        echo "Please set powerAutomate.triggerUrl after deploying your flow"
        exit 1
    fi
    
    local filename=$(basename "$file_path")
    
    echo "Uploading file: $filename"
    echo "Trigger URL: $trigger_url"
    
    # Create JSON payload
    local payload=$(cat <<EOL
{
    "FilePath": "/Knowledge_Base_Files/$filename",
    "FileName": "$filename"
}
EOL
)
    
    # Send HTTP request
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$trigger_url")
    
    echo "Response: $response"
    echo "Upload request sent successfully!"
}

# Show usage if no arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 [FILE_PATH]"
    echo "Example: $0 ~/Downloads/ec-synnex-701601-0708-0927.xls"
    echo "Or use default file from config: $0"
    exit 1
fi

upload_file "$1"
EOF

chmod +x "$BASE_DIR/scripts/simple-upload.sh"

print_status "Simple upload script created at: scripts/simple-upload.sh"
echo ""

# Show manual setup instructions
print_status "=== MANUAL SETUP INSTRUCTIONS ==="
echo ""
echo "Since CLI installation failed, follow these manual steps:"
echo ""

echo "1. FIND YOUR AGENT ID:"
echo "   a. Go to: https://powerautomate.microsoft.com"
echo "   b. Navigate to your Copilot Studio environment"
echo "   c. Find 'Nathan's Hardware Buddy v.1' agent"
echo "   d. Copy the Agent ID from the URL or agent properties"
echo ""

echo "2. DEPLOY THE POWER AUTOMATE FLOW:"
echo "   a. Go to: https://powerautomate.microsoft.com"
echo "   b. Click 'My flows' > 'Import' > 'Import Package (Legacy)'"
echo "   c. Upload file: $BASE_DIR/flows/copilot-knowledge-refresh-flow.json"
echo "   d. Configure connections:"
echo "      - Dataverse: Connect to your Dataverse environment"
echo "      - OneDrive for Business: Connect to your OneDrive"
echo "   e. Set the CopilotStudioAgentId parameter to your Agent ID"
echo "   f. Save the flow"
echo ""

echo "3. GET THE TRIGGER URL:"
echo "   a. Open your deployed flow"
echo "   b. Click on the 'Request' trigger (first step)"
echo "   c. Copy the 'HTTP POST URL'"
echo ""

echo "4. UPDATE CONFIGURATION:"
echo "   a. Edit: $BASE_DIR/config/config.json"
echo "   b. Set 'copilotStudio.agentId' to your Agent ID"
echo "   c. Set 'powerAutomate.triggerUrl' to your trigger URL"
echo ""

echo "5. TEST THE UPLOAD:"
echo "   ./scripts/simple-upload.sh ~/Downloads/ec-synnex-701601-0708-0927.xls"
echo ""

# Create a configuration helper
print_status "Creating configuration helper..."

cat > "$BASE_DIR/scripts/update-config.py" << 'EOF'
#!/usr/bin/env python3
"""
Configuration update helper for Copilot Studio Knowledge Refresh
"""

import json
import sys
import os

def update_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {config_path}")
        return False
    
    print("=== Copilot Studio Configuration Update ===")
    print()
    
    # Get Agent ID
    current_agent_id = config['copilotStudio']['agentId']
    print(f"Current Agent ID: {current_agent_id}")
    agent_id = input("Enter your Copilot Studio Agent ID: ").strip()
    if agent_id:
        config['copilotStudio']['agentId'] = agent_id
    
    # Get Environment ID
    current_env_id = config['copilotStudio']['environment']['id']
    print(f"Current Environment ID: {current_env_id}")
    env_id = input("Enter your Environment ID (optional): ").strip()
    if env_id:
        config['copilotStudio']['environment']['id'] = env_id
    
    # Get Trigger URL
    current_trigger_url = config['powerAutomate']['triggerUrl']
    print(f"Current Trigger URL: {current_trigger_url}")
    trigger_url = input("Enter your Power Automate trigger URL: ").strip()
    if trigger_url:
        config['powerAutomate']['triggerUrl'] = trigger_url
    
    # Save configuration
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\nConfiguration updated successfully!")
        print(f"Config file: {config_path}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to save configuration: {e}")
        return False

if __name__ == "__main__":
    if update_config():
        print("\nYou can now test the upload with:")
        print("./scripts/simple-upload.sh ~/Downloads/ec-synnex-701601-0708-0927.xls")
    else:
        sys.exit(1)
EOF

chmod +x "$BASE_DIR/scripts/update-config.py"

print_status "Configuration helper created at: scripts/update-config.py"
echo ""

print_status "=== QUICK CONFIGURATION ==="
echo ""
echo "Run this to update your configuration interactively:"
echo "python3 scripts/update-config.py"
echo ""

print_status "=== ALTERNATIVE APPROACHES ==="
echo ""
echo "If you prefer, you can also:"
echo "1. Use the Power Automate web interface entirely"
echo "2. Set up a OneDrive folder sync with Power Automate"
echo "3. Use SharePoint document library integration"
echo ""

print_status "Setup preparation completed!"
print_status "Follow the manual steps above to complete the setup."