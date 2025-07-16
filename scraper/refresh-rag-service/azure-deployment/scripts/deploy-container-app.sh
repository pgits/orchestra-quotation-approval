#!/bin/bash
# Deploy to Azure Container Apps (supports multi-arch better)

set -e

RESOURCE_GROUP="rg-copilot-refresh"
CONTAINER_APP_NAME="copilot-refresh-app"
CONTAINER_APP_ENV="copilot-refresh-env"
REGISTRY_NAME="copilotrefreshacr597769"
IMAGE_NAME="copilot-refresh-service:latest"

echo "Creating Container App Environment..."
az containerapp env create \
  --name "$CONTAINER_APP_ENV" \
  --resource-group "$RESOURCE_GROUP" \
  --location "eastus"

echo "Creating Container App..."
az containerapp create \
  --name "$CONTAINER_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$CONTAINER_APP_ENV" \
  --image "$REGISTRY_NAME.azurecr.io/$IMAGE_NAME" \
  --registry-server "$REGISTRY_NAME.azurecr.io" \
  --registry-username "$REGISTRY_NAME" \
  --registry-password "$(az acr credential show --name $REGISTRY_NAME --query 'passwords[0].value' -o tsv)" \
  --target-port 8080 \
  --ingress external \
  --query properties.configuration.ingress.fqdn \
  --cpu 1.0 \
  --memory 2.0Gi \
  --min-replicas 1 \
  --max-replicas 1 \
  --env-vars \
    AGENT_ID="e71b63c6-9653-f011-877a-000d3a593ad6" \
    ENVIRONMENT_ID="33a7afba-68df-4fb5-84ba-abd928569b69" \
    SHAREPOINT_SITE_URL="https://hexalinks.sharepoint.com/sites/QuotationsTeam" \
    SHAREPOINT_LIBRARY_NAME="Shared Documents" \
    SHAREPOINT_FOLDER_PATH="EC Synnex Files" \
    SHAREPOINT_TENANT="hexalinks" \
    APPINSIGHTS_INSTRUMENTATION_KEY="37d88369-a344-4309-8040-e3bd4de4218f" \
    AZURE_CLIENT_ID="8cb37433-9611-4b2c-95c5-873c7946fc84"

echo "Container App deployed successfully!"
echo "You can access the health check at: https://$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)"