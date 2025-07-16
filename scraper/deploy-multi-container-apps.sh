#!/bin/bash
# Deploy TD SYNNEX scraper with email verification service to Azure Container Apps

set -e

# Configuration
RESOURCE_GROUP="td-synnex-scraper-rg"
CONTAINER_APP_ENV="td-synnex-env"
REGISTRY_NAME="tdsynnexscraperacr"
LOCATION="eastus"

# Container Apps
SCRAPER_APP_NAME="td-synnex-web-scraper"
EMAIL_SERVICE_APP_NAME="email-verification-service"

# Image names
SCRAPER_IMAGE_NAME="td-synnex-web-scraper"
EMAIL_SERVICE_IMAGE_NAME="email-verification-service"
IMAGE_TAG="latest"

# Check if credentials are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <TDSYNNEX_USERNAME> <TDSYNNEX_PASSWORD>"
    echo "Example: $0 'your-username' 'your-password'"
    echo ""
    echo "Also ensure these environment variables are set:"
    echo "  AZURE_TENANT_ID"
    echo "  AZURE_CLIENT_ID"
    echo "  AZURE_CLIENT_SECRET"
    exit 1
fi

TDSYNNEX_USERNAME="$1"
TDSYNNEX_PASSWORD="$2"

# Validate Azure credentials
if [ -z "$AZURE_TENANT_ID" ] || [ -z "$AZURE_CLIENT_ID" ] || [ -z "$AZURE_CLIENT_SECRET" ]; then
    echo "❌ Missing Azure credentials for email service!"
    echo "Please set these environment variables:"
    echo "  export AZURE_TENANT_ID=your-tenant-id"
    echo "  export AZURE_CLIENT_ID=your-client-id"
    echo "  export AZURE_CLIENT_SECRET=your-client-secret"
    exit 1
fi

echo "🚀 Deploying TD SYNNEX Multi-Container Solution to Azure Container Apps..."

# Build and push email verification service image
echo "🔨 Building email verification service image..."
docker build --platform linux/amd64 -t $EMAIL_SERVICE_IMAGE_NAME:$IMAGE_TAG ./email-verification-service/

echo "🏷️ Tagging email service image for Azure Container Registry..."
docker tag $EMAIL_SERVICE_IMAGE_NAME:$IMAGE_TAG $REGISTRY_NAME.azurecr.io/$EMAIL_SERVICE_IMAGE_NAME:$IMAGE_TAG

echo "📤 Pushing email service image to Azure Container Registry..."
docker push $REGISTRY_NAME.azurecr.io/$EMAIL_SERVICE_IMAGE_NAME:$IMAGE_TAG

# Build and push main scraper image
echo "🔨 Building main scraper image..."
docker build --platform linux/amd64 -f Dockerfile.container-apps -t $SCRAPER_IMAGE_NAME:$IMAGE_TAG .

echo "🏷️ Tagging scraper image for Azure Container Registry..."
docker tag $SCRAPER_IMAGE_NAME:$IMAGE_TAG $REGISTRY_NAME.azurecr.io/$SCRAPER_IMAGE_NAME:$IMAGE_TAG

echo "📤 Pushing scraper image to Azure Container Registry..."
docker push $REGISTRY_NAME.azurecr.io/$SCRAPER_IMAGE_NAME:$IMAGE_TAG

# Get ACR credentials
echo "🔐 Getting Azure Container Registry credentials..."
ACR_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --query "passwords[0].value" -o tsv)

# Create Container Apps environment if it doesn't exist
echo "🌍 Creating Container Apps environment..."
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  2>/dev/null || echo "Environment already exists"

# Deploy Email Verification Service first
echo "📧 Deploying Email Verification Service..."

if az containerapp create \
  --name $EMAIL_SERVICE_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image $REGISTRY_NAME.azurecr.io/$EMAIL_SERVICE_IMAGE_NAME:$IMAGE_TAG \
  --registry-server $REGISTRY_NAME.azurecr.io \
  --registry-username $REGISTRY_NAME \
  --registry-password "$ACR_PASSWORD" \
  --target-port 5000 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 2 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    AZURE_TENANT_ID="$AZURE_TENANT_ID" \
    AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
    AZURE_CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
    OUTLOOK_USER_EMAIL="pgits@hexalinks.com" \
  2>/dev/null; then
  echo "✅ Email verification service created successfully"
else
  echo "📝 Email verification service exists, updating..."
  az containerapp update \
    --name $EMAIL_SERVICE_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image $REGISTRY_NAME.azurecr.io/$EMAIL_SERVICE_IMAGE_NAME:$IMAGE_TAG \
    --set-env-vars \
      AZURE_TENANT_ID="$AZURE_TENANT_ID" \
      AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
      AZURE_CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
      OUTLOOK_USER_EMAIL="pgits@hexalinks.com"
fi

# Wait for email service to be ready
echo "⏳ Waiting for email service to be ready..."
sleep 10

# Deploy Main Scraper Service
echo "🐳 Deploying Main Scraper Service..."

if az containerapp create \
  --name $SCRAPER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image $REGISTRY_NAME.azurecr.io/$SCRAPER_IMAGE_NAME:$IMAGE_TAG \
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
    EMAIL_SERVICE_URL="http://$EMAIL_SERVICE_APP_NAME" \
  2>/dev/null; then
  echo "✅ Main scraper service created successfully"
else
  echo "📝 Main scraper service exists, updating..."
  az containerapp update \
    --name $SCRAPER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image $REGISTRY_NAME.azurecr.io/$SCRAPER_IMAGE_NAME:$IMAGE_TAG \
    --set-env-vars \
      TDSYNNEX_USERNAME="$TDSYNNEX_USERNAME" \
      TDSYNNEX_PASSWORD="$TDSYNNEX_PASSWORD" \
      EMAIL_SERVICE_URL="http://$EMAIL_SERVICE_APP_NAME"
fi

# Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."
sleep 15

# Get the application URLs
echo "🔍 Getting application URLs..."
SCRAPER_URL=$(az containerapp show --name $SCRAPER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)
EMAIL_SERVICE_URL=$(az containerapp show --name $EMAIL_SERVICE_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)

if [ -z "$SCRAPER_URL" ]; then
  echo "❌ Failed to get scraper URL. Trying again..."
  sleep 5
  SCRAPER_URL=$(az containerapp show --name $SCRAPER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)
fi

echo ""
echo "✅ Multi-Container deployment completed!"
echo "🌐 Main Scraper URL: https://$SCRAPER_URL"
echo "📧 Email Service URL: https://$EMAIL_SERVICE_URL (internal only)"
echo ""
echo "🔥 FOR POWER AUTOMATE HTTP ACTION (UPDATED):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Method: POST"
echo "URI: https://$SCRAPER_URL/scrape"
echo "Headers: {\"Content-Type\": \"application/json\"}"
echo "Body: {\"username\": \"pgits@hexalinks.com\", \"password\": \"M1ddaugh@etan!\", \"test\": false, \"quotation_id\": \"@{triggerBody()?['quotation_id']}\"}"
echo "Note: Verification codes will now be automatically retrieved from email!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 API Endpoints:"
echo "  Main Scraper:"
echo "    Health Check: https://$SCRAPER_URL/health"
echo "    Scraping API: https://$SCRAPER_URL/scrape"
echo "    Status Check: https://$SCRAPER_URL/status"
echo "  Email Service (internal):"
echo "    Health Check: https://$EMAIL_SERVICE_URL/health"
echo "    Get Verification Code: https://$EMAIL_SERVICE_URL/verification-code"
echo "    Test Email: https://$EMAIL_SERVICE_URL/test-email"
echo ""
echo "🔧 Test the API:"
echo "curl -X GET https://$SCRAPER_URL/health"
echo ""
echo "curl -X POST https://$SCRAPER_URL/scrape \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"test\": true, \"quotation_id\": \"test-123\"}'"
echo ""
echo "📊 Monitor logs:"
echo "Main Scraper: az containerapp logs show --name $SCRAPER_APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo "Email Service: az containerapp logs show --name $EMAIL_SERVICE_APP_NAME --resource-group $RESOURCE_GROUP --follow"