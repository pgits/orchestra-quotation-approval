#!/bin/bash
# Azure Container Deployment Script for Knowledge Update Service

set -e

# Configuration
SERVICE_NAME="td-synnex-knowledge-update"
RESOURCE_GROUP="td-synnex-scraper-rg"
REGISTRY_NAME="tdsynnexscraperacr"
REGISTRY_URL="$REGISTRY_NAME.azurecr.io"
IMAGE_NAME="$SERVICE_NAME"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_error ".env file not found"
        print_error "Please copy .env.example to .env and configure with your credentials"
        exit 1
    fi
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI not found. Please install Azure CLI"
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker"
        exit 1
    fi
    
    # Check if logged into Azure
    if ! az account show &> /dev/null; then
        print_error "Not logged into Azure. Please run 'az login'"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image..."
    
    # Build Azure-optimized image for linux/amd64 platform
    docker build --platform linux/amd64 -f Dockerfile.azure -t "$IMAGE_NAME:$IMAGE_TAG" .
    
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully"
    else
        print_error "Docker build failed"
        exit 1
    fi
}

# Function to tag and push image
push_image() {
    print_status "Tagging and pushing image to Azure Container Registry..."
    
    # Tag for Azure Container Registry
    docker tag "$IMAGE_NAME:$IMAGE_TAG" "$REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG"
    
    # Login to Azure Container Registry
    az acr login --name "$REGISTRY_NAME"
    
    # Push image
    docker push "$REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG"
    
    if [ $? -eq 0 ]; then
        print_success "Image pushed successfully to $REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG"
    else
        print_error "Image push failed"
        exit 1
    fi
}

# Function to deploy to Azure Container Apps
deploy_container_app() {
    print_status "Deploying to Azure Container Apps..."
    
    # Check if container app exists
    if az containerapp show --name "$SERVICE_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        print_status "Updating existing container app..."
        
        az containerapp update \
            --name "$SERVICE_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --image "$REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG"
    else
        print_status "Creating new container app..."
        
        az containerapp create \
            --name "$SERVICE_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --environment "td-synnex-env" \
            --image "$REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG" \
            --registry-server "$REGISTRY_URL" \
            --registry-username "$REGISTRY_NAME" \
            --registry-password "$(az acr credential show --name $REGISTRY_NAME --query passwords[0].value --output tsv)" \
            --target-port 5000 \
            --ingress external \
            --min-replicas 1 \
            --max-replicas 3 \
            --cpu 1.0 \
            --memory 2Gi
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Container app deployed successfully"
        
        # Get the application URL
        APP_URL=$(az containerapp show \
            --name "$SERVICE_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --query "properties.configuration.ingress.fqdn" \
            --output tsv)
        
        if [ ! -z "$APP_URL" ]; then
            print_success "Application URL: https://$APP_URL"
            print_success "Health check: https://$APP_URL/health"
        fi
    else
        print_error "Container app deployment failed"
        exit 1
    fi
}

# Function to show help
show_help() {
    echo "Azure Deployment Script for TD SYNNEX Knowledge Update Service"
    echo ""
    echo "Usage: $0 [build|push|deploy|all|help]"
    echo ""
    echo "Commands:"
    echo "  build   - Build Docker image only"
    echo "  push    - Tag and push image to Azure Container Registry"
    echo "  deploy  - Deploy to Azure Container Apps"
    echo "  all     - Run build, push, and deploy (default)"
    echo "  help    - Show this help message"
    echo ""
    echo "Prerequisites:"
    echo "  1. Azure CLI installed and logged in"
    echo "  2. Docker installed"
    echo "  3. .env file configured with credentials"
    echo "  4. Azure Container Registry created"
    echo "  5. Resource group exists"
    echo ""
    echo "Configuration (edit this script to modify):"
    echo "  SERVICE_NAME: $SERVICE_NAME"
    echo "  RESOURCE_GROUP: $RESOURCE_GROUP"
    echo "  REGISTRY_NAME: $REGISTRY_NAME"
}

# Main script logic
case "${1:-all}" in
    "build")
        echo "🔨 Building Docker Image"
        echo "======================"
        check_prerequisites
        build_image
        ;;
    "push")
        echo "📤 Pushing to Container Registry"
        echo "==============================="
        check_prerequisites
        push_image
        ;;
    "deploy")
        echo "🚀 Deploying to Azure Container Apps"
        echo "==================================="
        check_prerequisites
        deploy_container_app
        ;;
    "all")
        echo "🚀 Full Deployment Pipeline"
        echo "=========================="
        check_prerequisites
        build_image
        push_image
        deploy_container_app
        print_success "Deployment pipeline completed successfully!"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac