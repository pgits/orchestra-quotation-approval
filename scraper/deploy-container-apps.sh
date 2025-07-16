#!/bin/bash
# Deploy TD SYNNEX scraper to Azure Container Apps for Copilot Studio integration

set -e

# Configuration
RESOURCE_GROUP="td-synnex-scraper-rg"
CONTAINER_APP_NAME="td-synnex-web-scraper"
CONTAINER_APP_ENV="td-synnex-env"
REGISTRY_NAME="tdsynnexscraperacr"
IMAGE_NAME="td-synnex-web-scraper"
IMAGE_TAG="latest"

# Check if credentials are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <TDSYNNEX_USERNAME> <TDSYNNEX_PASSWORD>"
    echo "Example: $0 'your-username' 'your-password'"
    exit 1
fi

TDSYNNEX_USERNAME="$1"
TDSYNNEX_PASSWORD="$2"

echo "🚀 Deploying TD SYNNEX Web Scraper to Azure Container Apps..."

# Build and push the web container image
echo "🔨 Building web container image..."
docker build --platform linux/amd64 -f Dockerfile.container-apps -t $IMAGE_NAME:$IMAGE_TAG .

echo "🏷️ Tagging image for Azure Container Registry..."
docker tag $IMAGE_NAME:$IMAGE_TAG $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG

echo "📤 Pushing image to Azure Container Registry..."
docker push $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG

# Get ACR credentials
echo "🔐 Getting Azure Container Registry credentials..."
ACR_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --query "passwords[0].value" -o tsv)

# Create Container Apps environment if it doesn't exist
echo "🌍 Creating Container Apps environment..."
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location eastus \
  2>/dev/null || echo "Environment already exists"

# Deploy or update the container app
echo "🐳 Deploying Container App..."

# Try to create new container app
if az containerapp create \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG \
  --registry-server $REGISTRY_NAME.azurecr.io \
  --registry-username $REGISTRY_NAME \
  --registry-password "$ACR_PASSWORD" \
  --target-port 8080 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 2.0 \
  --memory 4.0Gi \
  --env-vars \
    TDSYNNEX_USERNAME="$TDSYNNEX_USERNAME" \
    TDSYNNEX_PASSWORD="$TDSYNNEX_PASSWORD" \
  2>/dev/null; then
  echo "✅ Container app created successfully"
else
  echo "📝 Container app exists, updating..."
  az containerapp update \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG \
    --set-env-vars \
      TDSYNNEX_USERNAME="$TDSYNNEX_USERNAME" \
      TDSYNNEX_PASSWORD="$TDSYNNEX_PASSWORD"
fi

# Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."
sleep 10

# Get the application URL
echo "🔍 Getting application URL..."
APP_URL=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)

if [ -z "$APP_URL" ]; then
  echo "❌ Failed to get application URL. Trying again..."
  sleep 5
  APP_URL=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)
fi

echo ""
echo "✅ Container App deployment completed!"
echo "🌐 Application URL: https://$APP_URL"
echo ""
echo "🔥 FOR POWER AUTOMATE HTTP ACTION:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Method: POST"
echo "URI: https://$APP_URL/scrape"
echo "Headers: {\"Content-Type\": \"application/json\"}"
echo "Body: {\"username\": \"pgits@hexalinks.com\", \"password\": \"M1ddaugh@etan!\", \"test\": false, \"quotation_id\": \"@{triggerBody()?['quotation_id']}\"}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 All API Endpoints:"
echo "  Health Check: https://$APP_URL/health"
echo "  Scraping API: https://$APP_URL/scrape"
echo "  Status Check: https://$APP_URL/status"
echo ""
echo "🔧 Test the API:"
echo "curl -X GET https://$APP_URL/health"
echo ""
echo "curl -X POST https://$APP_URL/scrape \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"test\": true, \"quotation_id\": \"test-123\"}'"
echo ""
echo "📊 Monitor logs:"
echo "az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow"