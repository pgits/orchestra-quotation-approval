#!/bin/bash
# Simplified deployment script to handle CLI issues

set -e

RESOURCE_GROUP="rg-copilot-refresh"
LOCATION="eastus"
AGENT_ID="e71b63c6-9653-f011-877a-000d3a593ad6"
ENV_ID="33a7afba-68df-4fb5-84ba-abd928569b69"
SHAREPOINT_URL="https://hexalinks.sharepoint.com/sites/QuotationsTeam"

echo "Starting deployment..."

# Create resource group if it doesn't exist
echo "Creating resource group..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" || true

# Deploy infrastructure step by step
echo "Deploying Container Registry..."
az acr create \
  --resource-group "$RESOURCE_GROUP" \
  --name "copilotrefreshacr$(date +%s | tail -c 7)" \
  --sku Basic \
  --admin-enabled true

echo "Creating Managed Identity..."
az identity create \
  --resource-group "$RESOURCE_GROUP" \
  --name "copilot-refresh-identity"

echo "Creating Log Analytics Workspace..."
az monitor log-analytics workspace create \
  --resource-group "$RESOURCE_GROUP" \
  --workspace-name "copilot-refresh-logs"

echo "Creating Application Insights..."
az monitor app-insights component create \
  --app "copilot-refresh-insights" \
  --location "$LOCATION" \
  --resource-group "$RESOURCE_GROUP" \
  --workspace "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.OperationalInsights/workspaces/copilot-refresh-logs"

echo "Deployment completed successfully!"
echo "Resource Group: $RESOURCE_GROUP"
echo "Next step: Build and deploy the container"