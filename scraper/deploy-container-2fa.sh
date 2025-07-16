#!/bin/bash

# Deploy TD SYNNEX Scraper with 2FA support to Azure Container Instance
set -e

# Configuration
RESOURCE_GROUP="td-synnex-scraper-2fa-rg"
CONTAINER_NAME="td-synnex-scraper-2fa"
LOCATION="eastus"
IMAGE_NAME="td-synnex-scraper-2fa"
ACR_NAME="tdsynnexacr$(date +%s)"  # Unique ACR name

echo "🚀 Deploying TD SYNNEX Scraper with 2FA to Azure Container Instance"

# Create resource group if it doesn't exist
echo "Creating resource group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION

# Create Azure Container Registry
echo "Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true

# Get ACR login server and credentials
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

echo "ACR Login Server: $ACR_LOGIN_SERVER"

# Build and push Docker image
echo "Building Docker image with 2FA support..."
docker buildx build --platform linux/amd64 -t $IMAGE_NAME -f Dockerfile.container-with-2fa .

echo "Tagging image for ACR..."
docker tag $IMAGE_NAME $ACR_LOGIN_SERVER/$IMAGE_NAME:latest

echo "Logging into ACR..."
docker login $ACR_LOGIN_SERVER --username $ACR_USERNAME --password $ACR_PASSWORD

echo "Pushing image to ACR..."
docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:latest

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: .env file not found"
fi

# Deploy container instance
echo "Deploying container instance with 2FA support..."
az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --image $ACR_LOGIN_SERVER/$IMAGE_NAME:latest \
    --registry-login-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --dns-name-label $CONTAINER_NAME \
    --ports 5001 5002 5003 \
    --cpu 2 \
    --memory 4 \
    --os-type Linux \
    --restart-policy Always \
    --location $LOCATION \
    --environment-variables \
        TDSYNNEX_USERNAME="$TDSYNNEX_USERNAME" \
        TDSYNNEX_PASSWORD="$TDSYNNEX_PASSWORD" \
        EMAIL_USERNAME="$EMAIL_USERNAME" \
        EMAIL_PASSWORD="$EMAIL_PASSWORD" \
        IMAP_SERVER="$IMAP_SERVER" \
        SMTP_SERVER="$SMTP_SERVER" \
        SMTP_PORT="$SMTP_PORT" \
        LOG_LEVEL="$LOG_LEVEL" \
        RETRY_ATTEMPTS="$RETRY_ATTEMPTS" \
        TIMEOUT_MINUTES="$TIMEOUT_MINUTES" \
        RUN_MODE="test"

# Get container information
echo "Getting container information..."
CONTAINER_IP=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query ipAddress.ip --output tsv)
CONTAINER_FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query ipAddress.fqdn --output tsv)

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Container Information:"
echo "  Container IP: $CONTAINER_IP"
echo "  Container FQDN: $CONTAINER_FQDN"
echo "  2FA API: http://$CONTAINER_FQDN:5001"
echo ""
echo "🔧 2FA Testing:"
echo "  Health Check: curl -X GET http://$CONTAINER_FQDN:5001/health"
echo "  Start Listening: curl -X POST http://$CONTAINER_FQDN:5001/2fa-start"
echo "  Send Code: curl -X POST http://$CONTAINER_FQDN:5001/2fa-challenge \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"verificationId\": \"YOUR_CODE_HERE\"}'"
echo ""
echo "📊 Monitoring:"
echo "  Container Logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow"
echo "  2FA API Logs: az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command 'tail -f /app/logs/2fa_api.log'"
echo "  Scraper Logs: az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command 'tail -f /app/logs/scraper.log'"
echo ""
echo "🧪 Test 2FA Challenge:"
echo "  1. Wait for scraper to encounter 2FA challenge"
echo "  2. Check your email for verification code"
echo "  3. Submit code using the curl command above"
echo "  4. Watch scraper continue automatically"
echo ""
echo "🗑️ Cleanup (when done):"
echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"