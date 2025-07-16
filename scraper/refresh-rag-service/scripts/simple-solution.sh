#!/bin/bash
# Simplified solution - creates everything you need without complex imports

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

print_status "=== SIMPLIFIED COPILOT KNOWLEDGE REFRESH SOLUTION ==="
echo ""

# Create the proper package
print_status "Creating proper Power Automate package..."
python3 "$SCRIPT_DIR/create-flow-package.py"
echo ""

print_step "OPTION 1: Import Package"
echo "1. Go to: https://powerautomate.microsoft.com"
echo "2. Click 'My flows' → 'Import' → 'Import Package (Legacy)'"
echo "3. Upload: flows/CopilotKnowledgeRefreshFlow.zip"
echo "4. Configure connections when prompted"
echo ""

print_step "OPTION 2: Manual Creation (Recommended)"
echo "If package import fails, create the flow manually:"
echo "1. Read: docs/manual-flow-creation.md"
echo "2. Follow the step-by-step instructions"
echo "3. Much more reliable than package import"
echo ""

print_step "AFTER FLOW CREATION:"
echo "1. Get your Agent ID from Copilot Studio"
echo "2. Copy the HTTP trigger URL from your flow"
echo "3. Run: python3 scripts/config-wizard.py"
echo "4. Test: python3 scripts/upload-to-copilot.py ~/Downloads/ec-synnex-701601-0708-0927.xls"
echo ""

# Create a quick test script
cat > "$BASE_DIR/scripts/test-upload.sh" << 'EOF'
#!/bin/bash
# Quick test script for the upload

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILE_PATH="~/Downloads/ec-synnex-701601-0708-0927.xls"

echo "Testing upload with file: $FILE_PATH"
echo ""

if [ -f "$(eval echo $FILE_PATH)" ]; then
    python3 "$SCRIPT_DIR/upload-to-copilot.py" "$FILE_PATH"
else
    echo "ERROR: File not found: $FILE_PATH"
    echo "Please check the file path in config.json or provide the correct path"
    echo ""
    echo "Usage: $0 [file_path]"
    echo "Example: $0 ~/Downloads/my-file.xls"
    
    if [ -n "$1" ]; then
        python3 "$SCRIPT_DIR/upload-to-copilot.py" "$1"
    fi
fi
EOF

chmod +x "$BASE_DIR/scripts/test-upload.sh"

print_status "Quick test script created: scripts/test-upload.sh"
echo ""

print_status "=== NEXT STEPS ==="
echo "1. Try package import first (may work with proper format)"
echo "2. If import fails, use manual creation guide"
echo "3. Configure with: python3 scripts/config-wizard.py"
echo "4. Test with: ./scripts/test-upload.sh"
echo ""

print_status "All files ready! Choose your preferred approach above."