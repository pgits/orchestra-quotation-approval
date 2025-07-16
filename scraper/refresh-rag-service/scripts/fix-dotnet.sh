#!/bin/bash
# Quick fix for .NET runtime issues on macOS ARM64
# This script properly installs .NET runtime and Power Platform CLI

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

print_status "=== .NET Runtime Fix for macOS ARM64 ==="
echo ""

# Check current .NET status
print_status "Checking current .NET installation..."
if command -v dotnet >/dev/null 2>&1; then
    print_warning "Found existing .NET installation"
    dotnet --version 2>/dev/null || print_error "Existing .NET installation is broken"
else
    print_status "No .NET installation found"
fi

# Remove existing broken installations
print_status "Cleaning up existing .NET installations..."
if [ -d "$HOME/.dotnet" ]; then
    print_warning "Removing existing .NET directory: $HOME/.dotnet"
    rm -rf "$HOME/.dotnet"
fi

# Remove Homebrew .NET if it exists and is causing issues
if command -v brew >/dev/null 2>&1; then
    if brew list dotnet >/dev/null 2>&1; then
        print_warning "Removing Homebrew .NET installation..."
        brew uninstall dotnet --ignore-dependencies || true
    fi
fi

# Download and install .NET using official installer
print_status "Downloading .NET installer..."
curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh
chmod +x /tmp/dotnet-install.sh

print_status "Installing .NET 8.0 runtime and SDK..."
/tmp/dotnet-install.sh --channel 8.0 --runtime aspnetcore
/tmp/dotnet-install.sh --channel 8.0 --runtime dotnet  
/tmp/dotnet-install.sh --channel 8.0

# Set up environment variables
print_status "Setting up environment variables..."
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="$PATH:$HOME/.dotnet:$HOME/.dotnet/tools"

# Add to shell profile
if [ -f ~/.zprofile ]; then
    # Remove any existing DOTNET entries to avoid duplicates
    grep -v "DOTNET_ROOT\|/.dotnet" ~/.zprofile > /tmp/zprofile_clean || true
    mv /tmp/zprofile_clean ~/.zprofile
fi

echo 'export DOTNET_ROOT="$HOME/.dotnet"' >> ~/.zprofile
echo 'export PATH="$PATH:$HOME/.dotnet:$HOME/.dotnet/tools"' >> ~/.zprofile

# Test .NET installation
print_status "Testing .NET installation..."
if "$HOME/.dotnet/dotnet" --version >/dev/null 2>&1; then
    print_status ".NET installed successfully!"
    echo "Version: $($HOME/.dotnet/dotnet --version)"
else
    print_error ".NET installation failed!"
    exit 1
fi

# Install Power Platform CLI
print_status "Installing Power Platform CLI..."
"$HOME/.dotnet/dotnet" tool install --global Microsoft.PowerApps.CLI.Tool

# Test Power Platform CLI
print_status "Testing Power Platform CLI..."
if "$HOME/.dotnet/tools/pac" --version >/dev/null 2>&1; then
    print_status "Power Platform CLI installed successfully!"
    echo "Version: $($HOME/.dotnet/tools/pac --version)"
else
    print_error "Power Platform CLI installation failed!"
    exit 1
fi

# Clean up
rm -f /tmp/dotnet-install.sh

print_status "=== Installation Complete ==="
echo ""
echo "To use the tools in your current session, run:"
echo "export DOTNET_ROOT=\"\$HOME/.dotnet\""
echo "export PATH=\"\$PATH:\$HOME/.dotnet:\$HOME/.dotnet/tools\""
echo ""
echo "Or simply start a new terminal session."
echo ""
echo "Test the installation with:"
echo "pac --version"
echo ""
print_status "You can now continue with the setup!"