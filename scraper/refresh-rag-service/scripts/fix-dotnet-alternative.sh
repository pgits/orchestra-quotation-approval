#!/bin/bash
# Alternative fix for .NET runtime and Power Platform CLI issues on macOS ARM64
# This script uses alternative installation methods to avoid NuGet package issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "=== Alternative .NET Runtime and Power Platform CLI Fix ==="
echo ""

# Check if Homebrew is installed
if ! command -v brew >/dev/null 2>&1; then
    print_status "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Method 1: Try installing via Homebrew tap (often more stable)
print_status "Attempting to install Power Platform CLI via Homebrew..."

# Add Microsoft tap if not already added
if ! brew tap | grep -q microsoft/powerapps-cli; then
    print_status "Adding Microsoft PowerApps CLI tap..."
    brew tap microsoft/powerapps-cli
fi

# Install Power Platform CLI via Homebrew
if brew install powerapps-cli; then
    print_status "Power Platform CLI installed successfully via Homebrew!"
    
    # Test the installation
    if command -v pac >/dev/null 2>&1 && pac --version >/dev/null 2>&1; then
        print_status "Power Platform CLI is working correctly"
        echo "Version: $(pac --version)"
        exit 0
    else
        print_warning "Homebrew installation completed but pac command not working properly"
    fi
else
    print_warning "Homebrew installation failed, trying manual download..."
fi

# Method 2: Manual download and installation
print_status "Attempting manual download and installation..."

# Create a temporary directory for the download
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download the latest release directly from GitHub
print_status "Downloading Power Platform CLI from GitHub releases..."
LATEST_URL="https://api.github.com/repos/microsoft/powerplatform-build-tools/releases/latest"
DOWNLOAD_URL=$(curl -s "$LATEST_URL" | grep -o '"browser_download_url": "[^"]*powerapps-cli-[^"]*osx-arm64[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$DOWNLOAD_URL" ]; then
    print_error "Could not find ARM64 macOS download URL"
    # Fallback to Intel version with Rosetta
    print_status "Trying Intel version with Rosetta emulation..."
    DOWNLOAD_URL=$(curl -s "$LATEST_URL" | grep -o '"browser_download_url": "[^"]*powerapps-cli-[^"]*osx-x64[^"]*"' | head -1 | cut -d'"' -f4)
fi

if [ -n "$DOWNLOAD_URL" ]; then
    print_status "Downloading from: $DOWNLOAD_URL"
    curl -L -o powerapps-cli.tar.gz "$DOWNLOAD_URL"
    
    # Extract the archive
    print_status "Extracting Power Platform CLI..."
    tar -xzf powerapps-cli.tar.gz
    
    # Find the pac binary
    PAC_BINARY=$(find . -name "pac" -type f | head -1)
    
    if [ -n "$PAC_BINARY" ]; then
        # Install to /usr/local/bin
        print_status "Installing pac to /usr/local/bin..."
        sudo cp "$PAC_BINARY" /usr/local/bin/pac
        sudo chmod +x /usr/local/bin/pac
        
        # Test the installation
        if /usr/local/bin/pac --version >/dev/null 2>&1; then
            print_status "Power Platform CLI installed successfully via manual download!"
            echo "Version: $(/usr/local/bin/pac --version)"
            
            # Clean up
            cd /
            rm -rf "$TEMP_DIR"
            exit 0
        else
            print_warning "Manual installation completed but pac command not working properly"
        fi
    else
        print_error "Could not find pac binary in downloaded archive"
    fi
else
    print_error "Could not find download URL for Power Platform CLI"
fi

# Method 3: Alternative .NET installation with different approach
print_status "Attempting alternative .NET installation approach..."

# Clean up any existing installations
if [ -d "$HOME/.dotnet" ]; then
    print_warning "Removing existing .NET directory..."
    rm -rf "$HOME/.dotnet"
fi

# Try installing .NET via Homebrew first
print_status "Installing .NET via Homebrew..."
brew install --cask dotnet

# Wait for installation to complete
sleep 5

# Try installing Power Platform CLI with specific version
print_status "Trying to install Power Platform CLI with specific version..."
if command -v dotnet >/dev/null 2>&1; then
    # Try installing an older, more stable version
    dotnet tool install --global Microsoft.PowerApps.CLI.Tool --version 1.33.6 || \
    dotnet tool install --global Microsoft.PowerApps.CLI.Tool --version 1.32.5 || \
    dotnet tool install --global Microsoft.PowerApps.CLI.Tool --version 1.31.3
    
    # Test the installation
    if [ -f "$HOME/.dotnet/tools/pac" ] && "$HOME/.dotnet/tools/pac" --version >/dev/null 2>&1; then
        print_status "Power Platform CLI installed successfully with alternative method!"
        echo "Version: $($HOME/.dotnet/tools/pac --version)"
        
        # Set up environment
        export PATH="$PATH:$HOME/.dotnet/tools"
        echo 'export PATH="$PATH:$HOME/.dotnet/tools"' >> ~/.zprofile
        
        # Clean up
        cd /
        rm -rf "$TEMP_DIR"
        exit 0
    fi
fi

# Method 4: Use Azure CLI with Power Platform extension as fallback
print_status "Installing Azure CLI with Power Platform extension as fallback..."
if ! command -v az >/dev/null 2>&1; then
    brew install azure-cli
fi

# Install Power Platform extension
az extension add --name powerapps

print_status "Azure CLI with Power Platform extension installed!"
print_status "You can use 'az' commands instead of 'pac' for many operations."

# Clean up
cd /
rm -rf "$TEMP_DIR"

print_status "=== Installation Methods Attempted ==="
echo ""
print_status "Multiple installation methods have been tried. Check which one worked:"
echo ""
echo "1. Test Homebrew installation: pac --version"
echo "2. Test manual installation: /usr/local/bin/pac --version"
echo "3. Test .NET tools installation: ~/.dotnet/tools/pac --version"
echo "4. Test Azure CLI: az --version"
echo ""
print_status "If none work, you can still use the web interface for Power Automate deployment."