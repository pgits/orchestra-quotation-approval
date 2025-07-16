#!/bin/bash
# Final Solution - Works with Organizational Security Restrictions

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
print_error "🔒 ORGANIZATIONAL SECURITY DETECTED"
echo ""
print_warning "Your organization has security restrictions that prevent direct API access."
print_warning "Error Code 53003 indicates conditional access policies are blocking the Azure CLI."
echo ""

print_status "=== ALTERNATIVE SOLUTION ==="
echo ""
print_status "I've created a web-based solution that works within your security constraints:"
echo ""

print_step "1. Use Web Interface Upload (Recommended)"
echo "   This creates a guided web page for manual upload:"
echo "   python3 scripts/web-interface-upload.py ~/Downloads/ec-synnex-701601-0708-0927.xls"
echo ""

print_step "2. Direct Browser Upload"
echo "   Upload directly through Copilot Studio web interface:"
echo "   - Go to: https://copilotstudio.microsoft.com"
echo "   - Find: Nathan's Hardware Buddy v.1"
echo "   - Navigate to: Knowledge tab"
echo "   - Upload: ec-synnex-701601-0708-0927.xls"
echo ""

print_step "3. OneDrive + Power Automate Integration"
echo "   Set up automated sync through OneDrive:"
echo "   - Upload files to specific OneDrive folder"
echo "   - Power Automate monitors folder and updates knowledge base"
echo "   - Fully automated once configured"
echo ""

print_status "=== CURRENT CONFIGURATION ==="
print_status "Your Agent ID is configured: e71b63c6-9653-f011-877a-000d3a593ad6"
print_status "Environment ID: Default-33a7afba-68df-4fb5-84ba-abd928569b69"
echo ""

print_step "RECOMMENDED NEXT STEPS:"
echo ""
echo "1. Try the web interface upload:"
echo "   python3 scripts/web-interface-upload.py ~/Downloads/ec-synnex-701601-0708-0927.xls"
echo ""
echo "2. If that works, set up automation through OneDrive sync"
echo ""
echo "3. Contact your IT admin to request API access for full automation"
echo ""

print_status "The web interface approach will guide you through manual upload"
print_status "and provide options for future automation within your security constraints."