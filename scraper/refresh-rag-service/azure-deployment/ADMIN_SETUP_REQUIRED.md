# Admin Setup Required for GitHub Actions

## Issue
Your account doesn't have permission to create service principals for GitHub Actions authentication. You'll need someone with Azure AD admin privileges to complete this step.

## What You Need from Your Admin

### Option 1: Service Principal Creation (Recommended)

Ask your Azure AD admin to run these commands:

```bash
# Create service principal for GitHub Actions
az ad sp create-for-rbac \
  --name "github-actions-copilot-refresh" \
  --role contributor \
  --scopes /subscriptions/6971c576-2567-4149-8aa4-4e505806153d/resourceGroups/rg-copilot-refresh \
  --sdk-auth

# Grant additional permissions for Container Registry
az role assignment create \
  --assignee-object-id $(az ad sp show --id "github-actions-copilot-refresh" --query objectId -o tsv) \
  --role "AcrPush" \
  --scope /subscriptions/6971c576-2567-4149-8aa4-4e505806153d/resourceGroups/rg-copilot-refresh/providers/Microsoft.ContainerRegistry/registries/copilotrefreshacr597769
```

The admin should provide you with the JSON output that looks like:
```json
{
  "clientId": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
  "clientSecret": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "subscriptionId": "6971c576-2567-4149-8aa4-4e505806153d",
  "tenantId": "33a7afba-68df-4fb5-84ba-abd928569b69",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

### Option 2: Alternative Manual Build (No Admin Required)

If you can't get admin help, you can build the container manually on a Linux machine:

```bash
# On a Linux machine or VM
docker build --platform linux/amd64 -t copilot-refresh-service:amd64 .
docker tag copilot-refresh-service:amd64 copilotrefreshacr597769.azurecr.io/copilot-refresh-service:latest
az acr login --name copilotrefreshacr597769
docker push copilotrefreshacr597769.azurecr.io/copilot-refresh-service:latest

# Then update the container app
az containerapp update \
  --name copilot-refresh-app \
  --resource-group rg-copilot-refresh \
  --image copilotrefreshacr597769.azurecr.io/copilot-refresh-service:latest
```

## What You Can Do Now

### 1. Prepare Your GitHub Repository

```bash
# Create a new GitHub repository
# Name it: copilot-refresh-service
# Make it private

# Clone and set up the repository
git clone https://github.com/YOUR_USERNAME/copilot-refresh-service.git
cd copilot-refresh-service

# Copy all your files
cp -r /Users/petergits/dev/claude-orchestra/scraper/refresh-rag-service/azure-deployment/* .

# Add and commit
git add .
git commit -m "Initial commit with container deployment setup"
git push origin main
```

### 2. Set Up GitHub Secrets (Once You Have Service Principal)

Go to your GitHub repository > Settings > Secrets and variables > Actions

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `AZURE_CREDENTIALS` | (JSON from service principal creation) |
| `COPILOT_AGENT_ID` | `e71b63c6-9653-f011-877a-000d3a593ad6` |
| `COPILOT_ENVIRONMENT_ID` | `33a7afba-68df-4fb5-84ba-abd928569b69` |
| `SHAREPOINT_SITE_URL` | `https://hexalinks.sharepoint.com/sites/QuotationsTeam` |
| `SHAREPOINT_LIBRARY_NAME` | `Shared Documents` |
| `SHAREPOINT_FOLDER_PATH` | `EC Synnex Files` |
| `SHAREPOINT_TENANT` | `hexalinks` |
| `APPINSIGHTS_INSTRUMENTATION_KEY` | `37d88369-a344-4309-8040-e3bd4de4218f` |
| `AZURE_CLIENT_ID` | `8cb37433-9611-4b2c-95c5-873c7946fc84` |

### 3. Test the Current Setup

Even without the automated container, you can test the SharePoint integration:

```bash
# Check if the container app is running
az containerapp show --name copilot-refresh-app --resource-group rg-copilot-refresh

# Get the app URL
az containerapp show --name copilot-refresh-app --resource-group rg-copilot-refresh --query properties.configuration.ingress.fqdn -o tsv

# Check logs
az containerapp logs show --name copilot-refresh-app --resource-group rg-copilot-refresh --follow
```

## Next Steps

1. **Get admin help** to create the service principal
2. **Set up GitHub repository** with the provided files
3. **Configure GitHub secrets** once you have the service principal
4. **Run the GitHub Action** to deploy the x86_64 container
5. **Test the complete workflow** by uploading files to SharePoint

## Contact Information

When requesting admin help, provide them with:
- This document
- Your Azure subscription ID: `6971c576-2567-4149-8aa4-4e505806153d`
- Resource group name: `rg-copilot-refresh`
- The specific commands they need to run (shown above)

## Alternative: Quick Manual Fix

If you need this working immediately, you can manually upload the Excel file to SharePoint:

1. Go to: https://hexalinks.sharepoint.com/sites/QuotationsTeam
2. Navigate to: Shared Documents → EC Synnex Files
3. Upload: `ec-synnex-701601-0708-0927.xls`
4. Manually integrate with Nathan's Hardware Buddy v.1 in Copilot Studio

The infrastructure is ready - it's just the container build that needs the x86_64 architecture.