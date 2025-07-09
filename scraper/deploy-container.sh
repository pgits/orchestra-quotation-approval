#!/bin/bash
# Deploy TD SYNNEX scraper to Azure Container Instances

set -e

# Configuration
RESOURCE_GROUP="td-synnex-scraper-rg"
CONTAINER_NAME="td-synnex-azure-scraper"
REGISTRY_NAME="tdsynnexscraperacr"
IMAGE_NAME="td-synnex-azure-scraper"
IMAGE_TAG="latest"

# Check if credentials are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <TDSYNNEX_USERNAME> <TDSYNNEX_PASSWORD>"
    echo "Example: $0 'your-username' 'your-password'"
    exit 1
fi

TDSYNNEX_USERNAME="$1"
TDSYNNEX_PASSWORD="$2"

echo "🚀 Deploying TD SYNNEX scraper to Azure Container Instances..."

# Get ACR credentials
echo "🔐 Getting Azure Container Registry credentials..."
ACR_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --query "passwords[0].value" -o tsv)

# Clean up existing container if it exists
echo "🧹 Cleaning up existing container..."
az container delete --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --yes 2>/dev/null || true

# Create container instance
echo "🐳 Creating Azure Container Instance..."
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG \
  --registry-login-server $REGISTRY_NAME.azurecr.io \
  --registry-username $REGISTRY_NAME \
  --registry-password "$ACR_PASSWORD" \
  --cpu 2 \
  --memory 4 \
  --restart-policy OnFailure \
  --os-type Linux \
  --environment-variables \
    TDSYNNEX_USERNAME="$TDSYNNEX_USERNAME" \
    TDSYNNEX_PASSWORD="$TDSYNNEX_PASSWORD"

echo "✅ Container deployment completed!"
echo "📊 Container status:"
az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query "instanceView.state" -o tsv

echo ""
echo "📋 To check logs:"
echo "az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
echo ""
echo "📊 To check status:"
echo "az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query instanceView"