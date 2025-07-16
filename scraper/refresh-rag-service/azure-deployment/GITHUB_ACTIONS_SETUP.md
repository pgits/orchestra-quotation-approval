# GitHub Actions Setup for Container Deployment

## Overview

This guide will help you set up GitHub Actions to automatically build and deploy your Copilot Refresh Service container with x86_64 compatibility.

## Prerequisites

- GitHub repository with your code
- Azure subscription with deployed infrastructure
- Azure CLI installed locally

## Step 1: Create GitHub Repository

1. **Create a new GitHub repository** (if you don't have one):
   - Go to GitHub.com
   - Click "New repository"
   - Name it: `copilot-refresh-service`
   - Make it private
   - Initialize with README

2. **Clone the repository locally**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/copilot-refresh-service.git
   cd copilot-refresh-service
   ```

3. **Copy your project files**:
   ```bash
   # Copy the entire azure-deployment folder to your new repo
   cp -r /Users/petergits/dev/claude-orchestra/scraper/refresh-rag-service/azure-deployment/* .
   ```

## Step 2: Create Azure Service Principal

1. **Create service principal for GitHub Actions**:
   ```bash
   az ad sp create-for-rbac \
     --name "github-actions-copilot-refresh" \
     --role contributor \
     --scopes /subscriptions/6971c576-2567-4149-8aa4-4e505806153d/resourceGroups/rg-copilot-refresh \
     --sdk-auth
   ```

2. **Save the output** - you'll need it for GitHub secrets. It should look like:
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

## Step 3: Configure GitHub Repository Secrets

1. **Go to your GitHub repository** > Settings > Secrets and variables > Actions

2. **Add these Repository Secrets**:

   | Secret Name | Value |
   |-------------|-------|
   | `AZURE_CREDENTIALS` | (Entire JSON output from Step 2) |
   | `COPILOT_AGENT_ID` | `e71b63c6-9653-f011-877a-000d3a593ad6` |
   | `COPILOT_ENVIRONMENT_ID` | `33a7afba-68df-4fb5-84ba-abd928569b69` |
   | `SHAREPOINT_SITE_URL` | `https://hexalinks.sharepoint.com/sites/QuotationsTeam` |
   | `SHAREPOINT_LIBRARY_NAME` | `Shared Documents` |
   | `SHAREPOINT_FOLDER_PATH` | `EC Synnex Files` |
   | `SHAREPOINT_TENANT` | `hexalinks` |
   | `APPINSIGHTS_INSTRUMENTATION_KEY` | `37d88369-a344-4309-8040-e3bd4de4218f` |
   | `AZURE_CLIENT_ID` | `8cb37433-9611-4b2c-95c5-873c7946fc84` |

## Step 4: Create GitHub Actions Workflow

1. **Create the workflow directory**:
   ```bash
   mkdir -p .github/workflows
   ```

2. **Create the workflow file** `.github/workflows/build-and-deploy.yml`:

## Step 5: Grant Additional Permissions

1. **Grant Container Registry permissions**:
   ```bash
   az role assignment create \
     --assignee $(az ad sp show --id "github-actions-copilot-refresh" --query objectId -o tsv) \
     --role "AcrPush" \
     --scope /subscriptions/6971c576-2567-4149-8aa4-4e505806153d/resourceGroups/rg-copilot-refresh/providers/Microsoft.ContainerRegistry/registries/copilotrefreshacr597769
   ```

2. **Grant Container App permissions**:
   ```bash
   az role assignment create \
     --assignee $(az ad sp show --id "github-actions-copilot-refresh" --query objectId -o tsv) \
     --role "Contributor" \
     --scope /subscriptions/6971c576-2567-4149-8aa4-4e505806153d/resourceGroups/rg-copilot-refresh/providers/Microsoft.App/containerApps/copilot-refresh-app
   ```

## Step 6: Commit and Push Your Code

1. **Add all files to git**:
   ```bash
   git add .
   git commit -m "Add Copilot Refresh Service with GitHub Actions deployment"
   git push origin main
   ```

2. **GitHub Actions will automatically trigger** and build/deploy your container.

## Step 7: Monitor the Deployment

1. **Go to your GitHub repository** > Actions tab
2. **Click on the running workflow** to see progress
3. **Check the deployment logs** for any issues

## Step 8: Verify Deployment

1. **Get the container app URL**:
   ```bash
   az containerapp show \
     --name copilot-refresh-app \
     --resource-group rg-copilot-refresh \
     --query properties.configuration.ingress.fqdn -o tsv
   ```

2. **Test the health endpoint**:
   ```bash
   curl https://YOUR_APP_URL/health
   ```

3. **Check application logs**:
   ```bash
   az containerapp logs show \
     --name copilot-refresh-app \
     --resource-group rg-copilot-refresh \
     --follow
   ```

## Troubleshooting

### Common Issues:

1. **Authentication errors**: 
   - Check that AZURE_CREDENTIALS secret is valid
   - Verify service principal has correct permissions

2. **Container build failures**:
   - Check Dockerfile syntax
   - Verify all required files are in the container directory

3. **Deployment failures**:
   - Check Azure Container App logs
   - Verify all environment variables are set correctly

### Getting Help:

```bash
# Check service principal permissions
az role assignment list --assignee YOUR_SERVICE_PRINCIPAL_ID

# Check container app status
az containerapp show --name copilot-refresh-app --resource-group rg-copilot-refresh

# View detailed logs
az containerapp logs show --name copilot-refresh-app --resource-group rg-copilot-refresh --follow
```

## Next Steps

Once deployment is successful:
1. Test file upload to SharePoint
2. Verify container picks up and processes files
3. Confirm integration with Copilot Studio
4. Set up monitoring and alerts

## Manual Trigger

To manually trigger the deployment:
1. Go to GitHub repository > Actions
2. Click "Build and Deploy Copilot Refresh Service"
3. Click "Run workflow"
4. Select branch and click "Run workflow"