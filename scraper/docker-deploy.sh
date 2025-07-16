#!/bin/bash
# Deploy Azure Functions with Chrome support using Docker

set -e

# Configuration
RESOURCE_GROUP="td-synnex-scraper-rg"
FUNCTION_APP_NAME="tdsynnex-scraper-func"
REGISTRY_NAME="tdsynnexscraperacr"
IMAGE_NAME="tdsynnex-scraper-func"
IMAGE_TAG="latest"

echo "🐳 Deploying Azure Functions with Chrome support using Docker..."

# Step 1: Build Docker image
echo "📦 Building Docker image..."
docker build -f Dockerfile.azure -t $IMAGE_NAME:$IMAGE_TAG .

# Step 2: Tag image for Azure Container Registry
echo "🏷️  Tagging image for Azure Container Registry..."
docker tag $IMAGE_NAME:$IMAGE_TAG $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG

# Step 3: Login to Azure Container Registry
echo "🔐 Logging into Azure Container Registry..."
az acr login --name $REGISTRY_NAME

# Step 4: Push image to registry
echo "⬆️  Pushing image to Azure Container Registry..."
docker push $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG

# Step 5: Configure Function App to use container
echo "⚙️  Configuring Function App to use container..."
az functionapp config container set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG \
  --docker-registry-server-url https://$REGISTRY_NAME.azurecr.io

# Step 6: Restart Function App
echo "🔄 Restarting Function App..."
az functionapp restart --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP

echo "✅ Docker deployment completed successfully!"
echo "🌐 Function URL: https://$FUNCTION_APP_NAME.azurewebsites.net"
echo "📊 Test with: curl -X POST \"https://$FUNCTION_APP_NAME.azurewebsites.net/api/scrape?code=YOUR_CODE\" -d '{\"test\": true}'"