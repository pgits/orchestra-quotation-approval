#!/bin/bash
# macOS Setup Script for Copilot Studio Knowledge Base Upload Service
# Installs prerequisites and configures the environment

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Homebrew if not present
install_homebrew() {
    if ! command_exists brew; then
        print_status "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        print_status "Homebrew is already installed"
    fi
}

# Function to install Python 3 if not present
install_python() {
    if ! command_exists python3; then
        print_status "Installing Python 3..."
        brew install python3
    else
        print_status "Python 3 is already installed"
        python3 --version
    fi
}

# Function to install required packages
install_packages() {
    print_status "Installing required packages..."
    
    # Install jq for JSON processing
    if ! command_exists jq; then
        print_status "Installing jq..."
        brew install jq
    fi
    
    # Install curl (usually pre-installed on macOS)
    if ! command_exists curl; then
        print_status "Installing curl..."
        brew install curl
    fi
    
    # Install Python packages
    print_status "Installing Python packages..."
    pip3 install --user requests
}

# Function to install .NET runtime properly
install_dotnet_runtime() {
    print_status "Installing .NET runtime..."
    
    # Check if .NET is already installed and working
    if command_exists dotnet && dotnet --version >/dev/null 2>&1; then
        print_status ".NET is already installed and working"
        dotnet --version
        return 0
    fi
    
    # Remove existing .NET installations to avoid conflicts
    if [ -d "$HOME/.dotnet" ]; then
        print_warning "Removing existing .NET installation to avoid conflicts..."
        rm -rf "$HOME/.dotnet"
    fi
    
    # Install .NET via official installer (more reliable than Homebrew)
    print_status "Downloading and installing .NET 8.0 runtime..."
    
    # Download .NET 8.0 runtime for ARM64 macOS
    local dotnet_installer="/tmp/dotnet-install.sh"
    curl -fsSL https://dot.net/v1/dotnet-install.sh -o "$dotnet_installer"
    chmod +x "$dotnet_installer"
    
    # Install .NET runtime and SDK
    "$dotnet_installer" --channel 8.0 --runtime aspnetcore
    "$dotnet_installer" --channel 8.0 --runtime dotnet
    "$dotnet_installer" --channel 8.0
    
    # Add .NET to PATH
    echo 'export DOTNET_ROOT="$HOME/.dotnet"' >> ~/.zprofile
    echo 'export PATH="$PATH:$HOME/.dotnet:$HOME/.dotnet/tools"' >> ~/.zprofile
    
    # Export for current session
    export DOTNET_ROOT="$HOME/.dotnet"
    export PATH="$PATH:$HOME/.dotnet:$HOME/.dotnet/tools"
    
    # Verify installation
    if "$HOME/.dotnet/dotnet" --version >/dev/null 2>&1; then
        print_status ".NET installed successfully"
        "$HOME/.dotnet/dotnet" --version
    else
        print_error ".NET installation failed"
        return 1
    fi
}

# Function to install Power Platform CLI
install_power_platform_cli() {
    print_status "Installing Power Platform CLI..."
    
    # Install .NET runtime first
    install_dotnet_runtime
    
    # Check if pac is already installed and working
    if command_exists pac && pac --version >/dev/null 2>&1; then
        print_status "Power Platform CLI is already installed and working"
        pac --version
        return 0
    fi
    
    # Install Power Platform CLI using the .NET tool command
    print_status "Installing Power Platform CLI via .NET tool..."
    "$HOME/.dotnet/dotnet" tool install --global Microsoft.PowerApps.CLI.Tool
    
    # Verify installation
    if [ -f "$HOME/.dotnet/tools/pac" ]; then
        print_status "Power Platform CLI installed successfully"
        # Test the installation
        if "$HOME/.dotnet/tools/pac" --version >/dev/null 2>&1; then
            print_status "Power Platform CLI is working correctly"
            "$HOME/.dotnet/tools/pac" --version
        else
            print_error "Power Platform CLI installed but not working properly"
            return 1
        fi
    else
        print_error "Power Platform CLI installation failed"
        return 1
    fi
}

# Function to setup directory structure
setup_directories() {
    print_status "Setting up directory structure..."
    
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local base_dir="$(dirname "$script_dir")"
    
    # Create necessary directories
    mkdir -p "$base_dir/logs"
    mkdir -p "$base_dir/backup"
    
    print_status "Directory structure created"
}

# Function to create sample configuration
create_sample_config() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local config_file="$(dirname "$script_dir")/config/config.json"
    
    if [ -f "$config_file" ]; then
        print_warning "Configuration file already exists. Skipping creation."
        return
    fi
    
    print_status "Creating sample configuration..."
    
    cat > "$config_file" <<EOF
{
  "copilotStudio": {
    "agentName": "Nathan's Hardware Buddy v.1",
    "agentId": "YOUR_AGENT_ID_HERE",
    "environment": {
      "name": "YOUR_ENVIRONMENT_NAME",
      "id": "YOUR_ENVIRONMENT_ID",
      "region": "YOUR_REGION"
    }
  },
  "powerAutomate": {
    "flowName": "Copilot Knowledge Refresh Flow",
    "triggerUrl": "YOUR_FLOW_TRIGGER_URL_HERE",
    "resourceGroup": "YOUR_RESOURCE_GROUP",
    "subscriptionId": "YOUR_SUBSCRIPTION_ID"
  },
  "fileSettings": {
    "filePattern": "ec-synnex-",
    "maxFileSize": 536870912,
    "supportedExtensions": [".xls", ".xlsx", ".csv", ".pdf", ".docx", ".txt"],
    "localFilePath": "~/Downloads/ec-synnex-701601-0708-0927.xls"
  },
  "connections": {
    "dataverse": {
      "connectionName": "shared_commondataservice",
      "entityName": "msdyn_copilotcomponents"
    },
    "oneDrive": {
      "connectionName": "shared_onedriveforbusiness",
      "uploadFolder": "/Knowledge_Base_Files"
    }
  },
  "logging": {
    "level": "info",
    "enableAuditTrail": true,
    "retentionDays": 30
  }
}
EOF
    
    print_status "Sample configuration created at: $config_file"
}

# Function to show next steps
show_next_steps() {
    print_status "Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Update the configuration file with your actual values:"
    echo "   - Agent ID (use get-agent-id.sh to find it)"
    echo "   - Environment ID"
    echo "   - Power Automate trigger URL"
    echo ""
    echo "2. Deploy the Power Automate flow:"
    echo "   ./scripts/deploy-flow.sh"
    echo ""
    echo "3. Test the upload process:"
    echo "   ./scripts/upload-file.sh"
    echo ""
    echo "4. Set up a cron job for automatic uploads (optional):"
    echo "   crontab -e"
    echo "   # Add: 0 9 * * * /path/to/upload-file.sh"
    echo ""
}

# Main setup function
main() {
    print_status "Starting macOS setup for Copilot Studio Knowledge Base Upload Service..."
    
    # Install prerequisites
    install_homebrew
    install_python
    install_packages
    install_power_platform_cli
    
    # Setup directories
    setup_directories
    
    # Create sample configuration
    create_sample_config
    
    # Show next steps
    show_next_steps
}

# Run main function
main "$@"