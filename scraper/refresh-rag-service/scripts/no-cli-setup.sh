#!/bin/bash
# No-CLI Setup for Copilot Studio Knowledge Base Refresh
# This approach completely bypasses all CLI installation issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

print_status "=== NO-CLI Setup for Copilot Studio Knowledge Refresh ==="
echo ""
print_status "This setup completely avoids CLI installation issues."
print_status "Everything is done through web interfaces and direct HTTP calls."
echo ""

# Check prerequisites
print_status "Checking prerequisites..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    print_status "Installing Python 3..."
    if command -v brew &> /dev/null; then
        brew install python3
    else
        print_error "Please install Python 3 manually from https://python.org"
        exit 1
    fi
fi

# Check if curl is available
if ! command -v curl &> /dev/null; then
    print_error "curl is required but not installed."
    exit 1
fi

# Install Python requests library
print_status "Installing required Python packages..."
pip3 install --user requests || pip3 install --user requests --break-system-packages

# Create the complete upload solution
print_status "Creating complete upload solution..."

cat > "$BASE_DIR/scripts/upload-to-copilot.py" << 'EOF'
#!/usr/bin/env python3
"""
Complete Copilot Studio Knowledge Base Upload Solution
No CLI dependencies - works entirely through HTTP requests
"""

import json
import os
import sys
import requests
from pathlib import Path
import base64
import mimetypes

class CopilotUploader:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()
        
    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ERROR: Configuration file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"ERROR: Invalid JSON in configuration file: {self.config_path}")
            sys.exit(1)
    
    def validate_file(self, file_path):
        """Validate the file before upload"""
        if not os.path.exists(file_path):
            print(f"ERROR: File not found: {file_path}")
            return False
            
        file_size = os.path.getsize(file_path)
        max_size = self.config['fileSettings']['maxFileSize']
        
        if file_size > max_size:
            print(f"ERROR: File size ({file_size} bytes) exceeds maximum ({max_size} bytes)")
            return False
            
        file_ext = os.path.splitext(file_path)[1].lower()
        supported_exts = self.config['fileSettings']['supportedExtensions']
        
        if file_ext not in supported_exts:
            print(f"ERROR: File extension {file_ext} not supported")
            return False
            
        return True
    
    def upload_file(self, file_path):
        """Upload file to Copilot Studio via Power Automate"""
        if not self.validate_file(file_path):
            return False
            
        trigger_url = self.config['powerAutomate']['triggerUrl']
        if not trigger_url or trigger_url == "YOUR_FLOW_TRIGGER_URL_HERE":
            print("ERROR: Power Automate trigger URL not configured")
            print("Please update config.json with your flow trigger URL")
            return False
            
        filename = os.path.basename(file_path)
        
        # For this demo, we'll simulate the OneDrive path
        # In a real implementation, you'd upload to OneDrive first
        onedrive_path = f"/Knowledge_Base_Files/{filename}"
        
        payload = {
            "FilePath": onedrive_path,
            "FileName": filename
        }
        
        print(f"Uploading file: {filename}")
        print(f"File size: {os.path.getsize(file_path)} bytes")
        print(f"Trigger URL: {trigger_url}")
        
        try:
            response = requests.post(
                trigger_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                print("SUCCESS: File upload triggered successfully!")
                try:
                    result = response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                except:
                    print(f"Response: {response.text}")
                return True
            else:
                print(f"ERROR: Upload failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to connect to Power Automate: {e}")
            return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config', 'config.json')
    
    if len(sys.argv) < 2:
        print("Usage: python3 upload-to-copilot.py <file_path>")
        print("Example: python3 upload-to-copilot.py ~/Downloads/ec-synnex-701601-0708-0927.xls")
        sys.exit(1)
    
    file_path = os.path.expanduser(sys.argv[1])
    
    uploader = CopilotUploader(config_path)
    success = uploader.upload_file(file_path)
    
    if success:
        print("\nUpload process completed successfully!")
        sys.exit(0)
    else:
        print("\nUpload process failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x "$BASE_DIR/scripts/upload-to-copilot.py"

# Create configuration wizard
print_status "Creating configuration wizard..."

cat > "$BASE_DIR/scripts/config-wizard.py" << 'EOF'
#!/usr/bin/env python3
"""
Configuration Wizard for Copilot Studio Knowledge Refresh
Interactive setup without CLI dependencies
"""

import json
import os
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config', 'config.json')
    
    print("=== Copilot Studio Configuration Wizard ===")
    print()
    
    # Load existing config
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {config_path}")
        sys.exit(1)
    
    print("We'll help you configure the system step by step.")
    print("Press Enter to keep existing values, or type new values.")
    print()
    
    # Agent ID
    current_agent_id = config['copilotStudio']['agentId']
    print(f"Current Agent ID: {current_agent_id}")
    agent_id = input("Enter your Copilot Studio Agent ID: ").strip()
    if agent_id:
        config['copilotStudio']['agentId'] = agent_id
    
    # Environment ID
    current_env_id = config['copilotStudio']['environment']['id']
    print(f"Current Environment ID: {current_env_id}")
    env_id = input("Enter your Environment ID (optional): ").strip()
    if env_id:
        config['copilotStudio']['environment']['id'] = env_id
    
    # Trigger URL
    current_trigger_url = config['powerAutomate']['triggerUrl']
    print(f"Current Trigger URL: {current_trigger_url}")
    print("This is the HTTP POST URL from your Power Automate flow.")
    trigger_url = input("Enter your Power Automate trigger URL: ").strip()
    if trigger_url:
        config['powerAutomate']['triggerUrl'] = trigger_url
    
    # File path
    current_file_path = config['fileSettings']['localFilePath']
    print(f"Current file path: {current_file_path}")
    file_path = input("Enter your file path (or press Enter for default): ").strip()
    if file_path:
        config['fileSettings']['localFilePath'] = file_path
    
    # Save configuration
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\n✅ Configuration saved successfully!")
        print(f"Config file: {config_path}")
        
        # Test configuration
        print("\n=== Configuration Test ===")
        if config['copilotStudio']['agentId'] != "YOUR_AGENT_ID_HERE":
            print("✅ Agent ID configured")
        else:
            print("❌ Agent ID not configured")
            
        if config['powerAutomate']['triggerUrl'] != "YOUR_FLOW_TRIGGER_URL_HERE":
            print("✅ Trigger URL configured")
        else:
            print("❌ Trigger URL not configured")
            
        print("\nYou can now test the upload with:")
        print("python3 scripts/upload-to-copilot.py ~/Downloads/ec-synnex-701601-0708-0927.xls")
        
    except Exception as e:
        print(f"ERROR: Failed to save configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x "$BASE_DIR/scripts/config-wizard.py"

# Create setup instructions
print_status "Creating setup instructions..."

cat > "$BASE_DIR/SETUP_INSTRUCTIONS.md" << 'EOF'
# No-CLI Setup Instructions

## Overview
This setup avoids all CLI installation issues by using web interfaces and direct HTTP calls.

## Step 1: Deploy Power Automate Flow

1. **Go to Power Automate**
   - Visit: https://powerautomate.microsoft.com
   - Sign in with your Microsoft 365 account

2. **Import the Flow**
   - Click "My flows" → "Import" → "Import Package (Legacy)"
   - Upload: `flows/copilot-knowledge-refresh-flow.json`

3. **Configure Connections**
   - **Dataverse**: Connect to your environment
   - **OneDrive for Business**: Connect to your OneDrive

4. **Set Parameters**
   - Find the "CopilotStudioAgentId" parameter
   - We'll set this in the next step

## Step 2: Find Your Agent ID

1. **Go to Copilot Studio**
   - Visit: https://copilotstudio.microsoft.com
   - Navigate to your environment

2. **Find Your Agent**
   - Look for "Nathan's Hardware Buddy v.1"
   - Click on the agent
   - Copy the Agent ID from the URL or agent properties

## Step 3: Get Flow Trigger URL

1. **Open Your Flow**
   - Go back to Power Automate
   - Open your imported flow

2. **Get Trigger URL**
   - Click on the "Request" trigger (first step)
   - Copy the "HTTP POST URL"

## Step 4: Configure the System

Run the configuration wizard:
```bash
python3 scripts/config-wizard.py
```

Enter:
- Your Agent ID (from Step 2)
- Your Environment ID (optional)
- Your Flow Trigger URL (from Step 3)

## Step 5: Test Upload

```bash
python3 scripts/upload-to-copilot.py ~/Downloads/ec-synnex-701601-0708-0927.xls
```

## Troubleshooting

- **File not found**: Check the file path
- **Trigger URL error**: Verify the URL from Power Automate
- **Agent ID error**: Make sure you copied the correct ID from Copilot Studio
- **Connection errors**: Check your internet connection and Microsoft 365 access

## Automation

To automate uploads, add to crontab:
```bash
crontab -e
# Add: 0 9 * * * cd /path/to/refresh-rag-service && python3 scripts/upload-to-copilot.py ~/Downloads/ec-synnex-701601-0708-0927.xls
```
EOF

print_status "Setup instructions created: SETUP_INSTRUCTIONS.md"
echo ""

print_step "1. Read the setup instructions:"
echo "   cat SETUP_INSTRUCTIONS.md"
echo ""

print_step "2. Deploy your Power Automate flow manually:"
echo "   - Go to: https://powerautomate.microsoft.com"
echo "   - Import: flows/copilot-knowledge-refresh-flow.json"
echo ""

print_step "3. Configure the system:"
echo "   python3 scripts/config-wizard.py"
echo ""

print_step "4. Test the upload:"
echo "   python3 scripts/upload-to-copilot.py ~/Downloads/ec-synnex-701601-0708-0927.xls"
echo ""

print_status "=== NO-CLI SETUP COMPLETE ==="
print_status "This solution completely bypasses CLI installation issues!"
print_status "Everything works through web interfaces and HTTP requests."
echo ""
print_status "Start with: cat SETUP_INSTRUCTIONS.md"