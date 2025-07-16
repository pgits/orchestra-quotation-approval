#!/bin/bash

# Deploy mitmproxy test-proxy to Azure Container Instance
set -e

# Configuration
RESOURCE_GROUP="test-proxy-rg"
CONTAINER_NAME="test-proxy-2fa"
LOCATION="eastus"
IMAGE_NAME="test-proxy-mitm"
ACR_NAME="testproxyacr$(date +%s)"  # Unique ACR name

echo "🚀 Deploying mitmproxy test-proxy to Azure Container Instance"

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

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

echo "ACR Login Server: $ACR_LOGIN_SERVER"

# Build and push Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

echo "Tagging image for ACR..."
docker tag $IMAGE_NAME $ACR_LOGIN_SERVER/$IMAGE_NAME:latest

echo "Logging into ACR..."
docker login $ACR_LOGIN_SERVER --username $ACR_USERNAME --password $ACR_PASSWORD

echo "Pushing image to ACR..."
docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:latest

# Deploy container instance
echo "Deploying container instance..."
az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --image $ACR_LOGIN_SERVER/$IMAGE_NAME:latest \
    --registry-login-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --dns-name-label $CONTAINER_NAME \
    --ports 8080 8081 \
    --cpu 2 \
    --memory 4 \
    --os-type Linux \
    --restart-policy Always \
    --location $LOCATION

# Get container information
echo "Getting container information..."
CONTAINER_IP=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query ipAddress.ip --output tsv)
CONTAINER_FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query ipAddress.fqdn --output tsv)

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Connection Information:"
echo "  Container IP: $CONTAINER_IP"
echo "  Container FQDN: $CONTAINER_FQDN"
echo "  Proxy Server: http://$CONTAINER_FQDN:8080"
echo "  Web Interface: http://$CONTAINER_FQDN:8081"
echo ""
echo "🔧 Browser Configuration:"
echo "  1. Set your browser proxy to: $CONTAINER_FQDN:8080"
echo "  2. Download mitmproxy certificate from: http://$CONTAINER_FQDN:8081"
echo "  3. Install certificate in your browser"
echo ""
echo "📊 Monitoring:"
echo "  - Web Interface: http://$CONTAINER_FQDN:8081"
echo "  - Logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow"
echo ""
echo "🗑️ Cleanup (when done):"
echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"