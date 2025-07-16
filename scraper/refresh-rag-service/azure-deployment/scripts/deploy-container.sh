#!/bin/bash
# Build and deploy container to Azure Container Registry

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

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_DIR="$(dirname "$SCRIPT_DIR")/container"
DEPLOYMENT_INFO_FILE="$(dirname "$SCRIPT_DIR")/deployment-info.json"

# Default values
RESOURCE_GROUP=""
CONTAINER_TAG="latest"
FORCE_REBUILD=false

# Function to show usage
show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Optional Parameters:
    -g, --resource-group RESOURCE_GROUP    Azure resource group name (auto-detected if not provided)
    -t, --tag TAG                          Container image tag (default: latest)
    -f, --force                            Force rebuild even if image exists
    -h, --help                             Show this help message

Examples:
    $0                                     # Use auto-detected settings
    $0 -g "my-resource-group" -t "v1.0"    # Specify resource group and tag
    $0 --force                             # Force rebuild
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -t|--tag)
            CONTAINER_TAG="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_REBUILD=true
            shift
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

print_status "=== Container Build and Deployment ==="
echo ""

# Load deployment information
print_step "1. Loading Deployment Information"
if [ ! -f "$DEPLOYMENT_INFO_FILE" ]; then
    print_error "Deployment info file not found: $DEPLOYMENT_INFO_FILE"
    print_error "Please run deploy-infrastructure.sh first"
    exit 1
fi

# Parse deployment info
CONTAINER_REGISTRY_NAME=$(jq -r '.container_registry.name' "$DEPLOYMENT_INFO_FILE")
CONTAINER_REGISTRY_LOGIN_SERVER=$(jq -r '.container_registry.login_server' "$DEPLOYMENT_INFO_FILE")

if [ -z "$RESOURCE_GROUP" ]; then
    RESOURCE_GROUP=$(jq -r '.deployment.resource_group' "$DEPLOYMENT_INFO_FILE")
fi

print_status "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Container Registry: $CONTAINER_REGISTRY_LOGIN_SERVER"
echo "  Container Tag: $CONTAINER_TAG"
echo "  Force Rebuild: $FORCE_REBUILD"
echo ""

# Check prerequisites
print_step "2. Checking Prerequisites"

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker Desktop."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check Azure CLI
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check Azure authentication
if ! az account show &> /dev/null; then
    print_error "Not authenticated to Azure. Please run 'az login' first."
    exit 1
fi

# Check jq
if ! command -v jq &> /dev/null; then
    print_error "jq is not installed. Please install it first."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_status "Install with: brew install jq"
    else
        print_status "Install with: apt-get install jq"
    fi
    exit 1
fi

print_status "Prerequisites check passed"

# Login to Azure Container Registry
print_step "3. Authenticating to Container Registry"
print_status "Logging into Azure Container Registry..."
az acr login --name "$CONTAINER_REGISTRY_NAME"

# Check if image already exists
print_step "4. Checking Existing Images"
IMAGE_NAME="copilot-uploader"
FULL_IMAGE_NAME="$CONTAINER_REGISTRY_LOGIN_SERVER/$IMAGE_NAME:$CONTAINER_TAG"

IMAGE_EXISTS=false
if az acr repository show --name "$CONTAINER_REGISTRY_NAME" --image "$IMAGE_NAME:$CONTAINER_TAG" &> /dev/null; then
    IMAGE_EXISTS=true
    print_status "Image already exists: $FULL_IMAGE_NAME"
fi

# Build container if needed
if [ "$IMAGE_EXISTS" = false ] || [ "$FORCE_REBUILD" = true ]; then
    print_step "5. Building Container Image"
    
    if [ "$FORCE_REBUILD" = true ]; then
        print_status "Force rebuild requested, building new image..."
    else
        print_status "Image does not exist, building new image..."
    fi
    
    print_status "Building container image: $FULL_IMAGE_NAME"
    print_status "Container directory: $CONTAINER_DIR"
    
    # Build the container
    docker build \
        --tag "$FULL_IMAGE_NAME" \
        --platform linux/amd64 \
        "$CONTAINER_DIR"
    
    print_status "Container build completed successfully"
    
    # Push to registry
    print_step "6. Pushing to Container Registry"
    print_status "Pushing image to Azure Container Registry..."
    
    docker push "$FULL_IMAGE_NAME"
    
    print_status "Container push completed successfully"
else
    print_status "Image already exists and force rebuild not requested, skipping build"
fi

# Update container instance
print_step "7. Updating Container Instance"
CONTAINER_INSTANCE_NAME=$(jq -r '.deployment.resource_group' "$DEPLOYMENT_INFO_FILE" | sed 's/.*-//')
CONTAINER_INSTANCE_NAME="${CONTAINER_INSTANCE_NAME:-copilot-refresh}-container"

print_status "Checking if container instance exists..."
if az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_INSTANCE_NAME" &> /dev/null; then
    print_status "Restarting container instance to use new image..."
    az container restart --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_INSTANCE_NAME"
    print_status "Container instance restarted successfully"
else
    print_warning "Container instance not found. It will be created with the new image on next infrastructure deployment."
fi

# Display container logs
print_step "8. Checking Container Status"
print_status "Waiting for container to start..."
sleep 30

print_status "Recent container logs:"
az container logs --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_INSTANCE_NAME" --tail 20 || true

# Get container instance details
print_step "9. Container Instance Information"
CONTAINER_FQDN=$(az container show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_INSTANCE_NAME" \
    --query ipAddress.fqdn -o tsv 2>/dev/null || echo "N/A")

CONTAINER_STATE=$(az container show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_INSTANCE_NAME" \
    --query containers[0].instanceView.currentState.state -o tsv 2>/dev/null || echo "Unknown")

print_status ""
print_status "=== CONTAINER DEPLOYMENT COMPLETED ==="
print_status ""
print_status "Container Information:"
print_status "  Image: $FULL_IMAGE_NAME"
print_status "  Container Instance: $CONTAINER_INSTANCE_NAME"
print_status "  State: $CONTAINER_STATE"
print_status "  FQDN: $CONTAINER_FQDN"
print_status ""

if [ "$CONTAINER_FQDN" != "N/A" ]; then
    print_status "Health Check URL: http://$CONTAINER_FQDN:8080/health"
    print_status "Status URL: http://$CONTAINER_FQDN:8080/status"
    print_status ""
    
    # Test health endpoint
    print_status "Testing health endpoint..."
    if curl -s -f "http://$CONTAINER_FQDN:8080/health" > /dev/null; then
        print_status "✅ Health check passed"
    else
        print_warning "⚠️  Health check failed (container may still be starting)"
    fi
fi

print_status "Next Steps:"
print_status "1. Upload a test file to SharePoint: $SHAREPOINT_SITE_URL"
print_status "2. Monitor container logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_INSTANCE_NAME --follow"
print_status "3. Check Application Insights for detailed monitoring"
print_status ""
print_status "Container deployment completed successfully!"