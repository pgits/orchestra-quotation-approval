#!/bin/bash
# Deploy Azure infrastructure for Copilot Knowledge Refresh Service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Default values
RESOURCE_GROUP=""
LOCATION="eastus"
RESOURCE_PREFIX="copilot-refresh"
SHAREPOINT_TENANT="hexalinks"
SHAREPOINT_SITE_URL="https://hexalinks.sharepoint.com/sites/QuotationsTeam"
AGENT_ID="e71b63c6-9653-f011-877a-000d3a593ad6"
ENVIRONMENT_ID="Default-33a7afba-68df-4fb5-84ba-abd928569b69"

# Function to show usage
show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Required Parameters:
    -g, --resource-group RESOURCE_GROUP    Azure resource group name

Optional Parameters (defaults configured for Hexalinks):
    -t, --tenant SHAREPOINT_TENANT         SharePoint tenant name (default: hexalinks)
    -s, --site-url SHAREPOINT_SITE_URL     Full SharePoint site URL (default: Hexalinks site)
    -l, --location LOCATION                Azure region (default: eastus)
    -p, --prefix PREFIX                    Resource name prefix (default: copilot-refresh)
    -a, --agent-id AGENT_ID                Copilot Studio Agent ID (default: configured)
    -e, --environment-id ENV_ID            Copilot Studio Environment ID (default: configured)
    -h, --help                             Show this help message

Examples:
    $0 -g "rg-copilot-refresh"                                      # Use Hexalinks defaults
    $0 --resource-group "rg-copilot" --location "westus2"          # Use Hexalinks defaults with different location
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -p|--prefix)
            RESOURCE_PREFIX="$2"
            shift 2
            ;;
        -t|--tenant)
            SHAREPOINT_TENANT="$2"
            shift 2
            ;;
        -s|--site-url)
            SHAREPOINT_SITE_URL="$2"
            shift 2
            ;;
        -a|--agent-id)
            AGENT_ID="$2"
            shift 2
            ;;
        -e|--environment-id)
            ENVIRONMENT_ID="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown argument: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$RESOURCE_GROUP" ]; then
    print_error "Missing required parameter: resource-group"
    show_usage
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BICEP_DIR="$(dirname "$SCRIPT_DIR")/infrastructure/bicep"

print_status "=== Azure Infrastructure Deployment ==="
echo ""
print_status "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Resource Prefix: $RESOURCE_PREFIX"
echo "  SharePoint Tenant: $SHAREPOINT_TENANT"
echo "  SharePoint Site URL: $SHAREPOINT_SITE_URL"
echo "  Agent ID: $AGENT_ID"
echo "  Environment ID: $ENVIRONMENT_ID"
echo ""

# Check if Azure CLI is installed and authenticated
print_step "1. Checking Azure CLI"
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    print_status "Install guide: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check Azure authentication
print_status "Checking Azure authentication..."
if ! az account show &> /dev/null; then
    print_error "Not authenticated to Azure. Please run 'az login' first."
    exit 1
fi

# Get current subscription info
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
print_status "Using subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"

# Check if resource group exists, create if not
print_step "2. Setting up Resource Group"
if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_status "Resource group '$RESOURCE_GROUP' already exists"
else
    print_status "Creating resource group '$RESOURCE_GROUP' in '$LOCATION'"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
fi

# Deploy Bicep template
print_step "3. Deploying Azure Infrastructure"
print_status "Deploying Bicep template..."

DEPLOYMENT_NAME="copilot-refresh-$(date +%Y%m%d-%H%M%S)"

az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$BICEP_DIR/main.bicep" \
    --name "$DEPLOYMENT_NAME" \
    --parameters \
        resourcePrefix="$RESOURCE_PREFIX" \
        location="$LOCATION" \
        sharePointTenant="$SHAREPOINT_TENANT" \
        sharePointSiteUrl="$SHAREPOINT_SITE_URL" \
        agentId="$AGENT_ID" \
        environmentId="$ENVIRONMENT_ID"

# Get deployment outputs
print_step "4. Retrieving Deployment Information"
CONTAINER_REGISTRY_NAME=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --query properties.outputs.containerRegistryName.value -o tsv)

CONTAINER_REGISTRY_LOGIN_SERVER=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --query properties.outputs.containerRegistryLoginServer.value -o tsv)

MANAGED_IDENTITY_ID=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --query properties.outputs.managedIdentityId.value -o tsv)

MANAGED_IDENTITY_CLIENT_ID=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --query properties.outputs.managedIdentityClientId.value -o tsv)

APPINSIGHTS_KEY=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --query properties.outputs.applicationInsightsInstrumentationKey.value -o tsv)

# Save deployment information
print_step "5. Saving Deployment Information"
DEPLOYMENT_INFO_FILE="$SCRIPT_DIR/../deployment-info.json"

cat > "$DEPLOYMENT_INFO_FILE" <<EOF
{
    "deployment": {
        "name": "$DEPLOYMENT_NAME",
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "resource_group": "$RESOURCE_GROUP",
        "location": "$LOCATION"
    },
    "container_registry": {
        "name": "$CONTAINER_REGISTRY_NAME",
        "login_server": "$CONTAINER_REGISTRY_LOGIN_SERVER"
    },
    "managed_identity": {
        "id": "$MANAGED_IDENTITY_ID",
        "client_id": "$MANAGED_IDENTITY_CLIENT_ID"
    },
    "configuration": {
        "resource_prefix": "$RESOURCE_PREFIX",
        "sharepoint_tenant": "$SHAREPOINT_TENANT",
        "sharepoint_site_url": "$SHAREPOINT_SITE_URL",
        "agent_id": "$AGENT_ID",
        "environment_id": "$ENVIRONMENT_ID",
        "appinsights_key": "$APPINSIGHTS_KEY"
    }
}
EOF

print_status "Deployment information saved to: $DEPLOYMENT_INFO_FILE"

# Configure additional permissions
print_step "6. Configuring Additional Permissions"
print_status "Setting up Microsoft Graph API permissions for managed identity..."

# Note: Some permissions may need to be granted manually in Azure Portal
print_warning "Some permissions may require manual configuration in Azure Portal:"
print_warning "1. Go to Azure Active Directory > App registrations"
print_warning "2. Find the managed identity application"
print_warning "3. Add Microsoft Graph API permissions:"
print_warning "   - Sites.Read.All (Application permission)"
print_warning "   - Files.Read.All (Application permission)"
print_warning "4. Grant admin consent for the permissions"

print_status ""
print_status "=== DEPLOYMENT COMPLETED SUCCESSFULLY ==="
print_status ""
print_status "Next Steps:"
print_status "1. Configure API permissions in Azure Portal (see warnings above)"
print_status "2. Run container deployment: ./deploy-container.sh"
print_status "3. Test the deployment: ./test-deployment.sh"
print_status ""
print_status "Important Information:"
print_status "  Resource Group: $RESOURCE_GROUP"
print_status "  Container Registry: $CONTAINER_REGISTRY_LOGIN_SERVER"
print_status "  Managed Identity: $MANAGED_IDENTITY_CLIENT_ID"
print_status "  Application Insights Key: $APPINSIGHTS_KEY"
print_status ""
print_status "Deployment info saved to: $DEPLOYMENT_INFO_FILE"