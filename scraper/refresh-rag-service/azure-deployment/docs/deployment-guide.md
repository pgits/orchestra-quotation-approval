# Azure Deployment Guide

This guide provides step-by-step instructions for deploying the Copilot Studio Knowledge Refresh Service to Azure.

## Prerequisites

Before starting, ensure you have:

- **Azure subscription** with Owner or Contributor access
- **Microsoft 365 admin access** for SharePoint site creation
- **Azure CLI** installed and authenticated
- **Docker Desktop** installed and running
- **jq** installed for JSON processing
- **PowerShell** (for SharePoint setup)

## Installation Check

Run this script to verify all prerequisites:

```bash
#!/bin/bash
# Check prerequisites
echo "Checking prerequisites..."

# Check Azure CLI
if command -v az &> /dev/null; then
    echo "✅ Azure CLI installed: $(az version --query '\"azure-cli\"' -o tsv)"
else
    echo "❌ Azure CLI not found. Install from: https://docs.microsoft.com/en-us/cli/azure/"
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker installed: $(docker --version)"
else
    echo "❌ Docker not found. Install Docker Desktop"
fi

# Check jq
if command -v jq &> /dev/null; then
    echo "✅ jq installed: $(jq --version)"
else
    echo "❌ jq not found. Install with: brew install jq (macOS) or apt-get install jq (Linux)"
fi

# Check PowerShell
if command -v pwsh &> /dev/null; then
    echo "✅ PowerShell installed: $(pwsh --version)"
else
    echo "❌ PowerShell not found. Install from: https://github.com/PowerShell/PowerShell"
fi

# Check Azure authentication
if az account show &> /dev/null; then
    echo "✅ Azure CLI authenticated"
else
    echo "❌ Azure CLI not authenticated. Run: az login"
fi

# Check Docker daemon
if docker info &> /dev/null; then
    echo "✅ Docker daemon running"
else
    echo "❌ Docker daemon not running. Start Docker Desktop"
fi
```

## Deployment Steps

### Step 1: Create SharePoint Site

First, create the SharePoint site to store your ec-synnex files:

```bash
# Follow the SharePoint setup guide
cat docs/sharepoint-setup.md
```

**Manual Steps:**
1. Follow the PowerShell script in `docs/sharepoint-setup.md` to create the SharePoint site
2. Note the SharePoint site URL and tenant name
3. Verify you can upload files to the "EC Synnex Files" library

**Expected Output:**
- SharePoint site URL: `https://yourtenant.sharepoint.com/sites/refresh-synnex-data`
- Document library: "EC Synnex Files"
- Upload permissions verified

### Step 2: Deploy Azure Infrastructure

Deploy the Azure resources using the infrastructure script:

```bash
cd azure-deployment

# Deploy infrastructure
./scripts/deploy-infrastructure.sh \
    --resource-group "rg-copilot-refresh" \
    --tenant "yourtenant" \
    --site-url "https://yourtenant.sharepoint.com/sites/refresh-synnex-data"
```

**What this creates:**
- Azure Container Registry
- Managed Identity with proper permissions
- Container Instance (initially stopped)
- Log Analytics Workspace
- Application Insights
- Role assignments for Power Platform and SharePoint access

**Expected Output:**
```
=== DEPLOYMENT COMPLETED SUCCESSFULLY ===

Next Steps:
1. Configure API permissions in Azure Portal (see warnings above)
2. Run container deployment: ./deploy-container.sh
3. Test the deployment: ./test-deployment.sh

Important Information:
  Resource Group: rg-copilot-refresh
  Container Registry: copilotrefreshacr123456.azurecr.io
  Managed Identity: 12345678-1234-1234-1234-123456789012
  Application Insights Key: abc123def456...
```

### Step 3: Configure API Permissions

**Manual Step - Required:**

The managed identity needs additional permissions that must be granted manually:

1. **Go to Azure Portal** → **Azure Active Directory** → **App registrations**
2. **Switch to "All applications"** tab
3. **Find your managed identity** (search for your resource group name)
4. **Go to API permissions** → **Add a permission**
5. **Add Microsoft Graph permissions:**
   - `Sites.Read.All` (Application permission)
   - `Files.Read.All` (Application permission)
   - `Sites.ReadWrite.All` (Application permission) - for moving files
6. **Click "Grant admin consent"** for your organization
7. **Verify permissions show "Granted"** status

**PowerShell Alternative:**
```powershell
# Get the managed identity
$managedIdentity = Get-AzADServicePrincipal -DisplayName "your-managed-identity-name"

# Add Microsoft Graph permissions (requires PowerShell with Microsoft.Graph module)
Connect-MgGraph -Scopes "Application.ReadWrite.All"
New-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $managedIdentity.Id -PrincipalId $managedIdentity.Id -AppRoleId "332a536c-c7ef-4017-ab91-336970924f0d" -ResourceId (Get-MgServicePrincipal -Filter "appId eq '00000003-0000-0000-c000-000000000000'").Id
```

### Step 4: Build and Deploy Container

Build the container image and deploy to Azure Container Registry:

```bash
# Build and deploy container
./scripts/deploy-container.sh
```

**What this does:**
- Builds the Docker container locally
- Pushes to Azure Container Registry
- Updates the Container Instance
- Restarts the service

**Expected Output:**
```
=== CONTAINER DEPLOYMENT COMPLETED ===

Container Information:
  Image: copilotrefreshacr123456.azurecr.io/copilot-uploader:latest
  Container Instance: copilot-refresh-container
  State: Running
  FQDN: copilot-refresh-container.eastus.azurecontainer.io

Health Check URL: http://copilot-refresh-container.eastus.azurecontainer.io:8080/health
Status URL: http://copilot-refresh-container.eastus.azurecontainer.io:8080/status
```

### Step 5: Test the Deployment

Test that everything is working:

```bash
# Test script (to be created)
./scripts/test-deployment.sh
```

**Manual Testing:**
1. **Check container health:**
   ```bash
   curl http://your-container-fqdn:8080/health
   ```

2. **Upload test file to SharePoint:**
   - Go to your SharePoint site
   - Upload a file named `ec-synnex-test.xls` to the "EC Synnex Files" library

3. **Monitor container logs:**
   ```bash
   az container logs --resource-group "rg-copilot-refresh" --name "copilot-refresh-container" --follow
   ```

4. **Check Copilot Studio:**
   - Go to https://copilotstudio.microsoft.com
   - Open "Nathan's Hardware Buddy v.1"
   - Check the Knowledge section for the uploaded file

## Environment Variables

The container uses these environment variables (automatically configured):

```bash
# Copilot Studio Configuration
AGENT_ID="e71b63c6-9653-f011-877a-000d3a593ad6"
ENVIRONMENT_ID="Default-33a7afba-68df-4fb5-84ba-abd928569b69"

# SharePoint Configuration
SHAREPOINT_SITE_URL="https://yourtenant.sharepoint.com/sites/refresh-synnex-data"
SHAREPOINT_LIBRARY_NAME="EC Synnex Files"
SHAREPOINT_TENANT="yourtenant"

# File Processing Configuration
FILE_PATTERN="ec-synnex-"
SUPPORTED_EXTENSIONS=".xls,.xlsx"
MAX_FILE_SIZE="536870912"  # 512MB

# Monitoring Configuration
CHECK_INTERVAL="300"  # 5 minutes
RETRY_ATTEMPTS="3"
RETRY_DELAY="60"  # 1 minute

# Azure Configuration
AZURE_SUBSCRIPTION_ID="your-subscription-id"
AZURE_RESOURCE_GROUP="rg-copilot-refresh"
APPINSIGHTS_INSTRUMENTATION_KEY="your-app-insights-key"
```

## Monitoring and Logging

### Application Insights

View detailed telemetry in Azure Portal:
1. Go to your Application Insights resource
2. Check "Live Metrics" for real-time monitoring
3. Use "Logs" to query custom telemetry

### Container Logs

View container logs:
```bash
# Real-time logs
az container logs --resource-group "rg-copilot-refresh" --name "copilot-refresh-container" --follow

# Recent logs
az container logs --resource-group "rg-copilot-refresh" --name "copilot-refresh-container" --tail 50
```

### Health Endpoints

The container exposes these endpoints:
- `http://container-fqdn:8080/health` - Health check
- `http://container-fqdn:8080/status` - Detailed status
- `http://container-fqdn:8080/metrics` - Metrics for monitoring

## Troubleshooting

### Common Issues

**1. Container fails to start**
```bash
# Check container logs
az container logs --resource-group "rg-copilot-refresh" --name "copilot-refresh-container"

# Common causes:
# - Missing API permissions
# - Invalid SharePoint URL
# - Network connectivity issues
```

**2. SharePoint access denied**
```bash
# Check managed identity permissions
az role assignment list --assignee "managed-identity-client-id"

# Verify API permissions in Azure Portal
```

**3. Copilot Studio upload fails**
```bash
# Check Power Platform permissions
# Verify agent ID is correct
# Check Application Insights logs
```

**4. Files not being processed**
```bash
# Check file naming pattern
# Verify file is in correct SharePoint library
# Check container logs for errors
```

### Debug Commands

```bash
# Check resource group resources
az resource list --resource-group "rg-copilot-refresh" --output table

# Check container instance details
az container show --resource-group "rg-copilot-refresh" --name "copilot-refresh-container"

# Check managed identity
az identity show --resource-group "rg-copilot-refresh" --name "copilot-refresh-identity"

# Check container registry
az acr repository list --name "copilotrefreshacr123456"
```

## Scaling and Production Considerations

### High Availability

For production deployments, consider:
- **Azure Container Apps** instead of Container Instances
- **Multiple regions** for redundancy
- **Azure Service Bus** for reliable message processing
- **Azure Functions** for event-driven processing

### Security

- **Key Vault** for sensitive configuration
- **Private endpoints** for network isolation
- **Network security groups** for access control
- **Azure AD Conditional Access** policies

### Cost Optimization

- **Container Apps** with consumption billing
- **Spot instances** for non-critical workloads
- **Resource cleanup** for unused resources
- **Monitoring** to optimize resource usage

## Maintenance

### Regular Tasks

1. **Monitor container health** weekly
2. **Check Application Insights** for errors
3. **Review processed files** in SharePoint
4. **Update container image** monthly
5. **Backup configuration** regularly

### Updates

To update the container:
```bash
# Build new version
./scripts/deploy-container.sh --tag "v1.1" --force

# Test the update
./scripts/test-deployment.sh
```

## Support

For issues:
1. Check the troubleshooting section above
2. Review container logs and Application Insights
3. Verify all manual configuration steps were completed
4. Check Azure service health for any outages

## Security Considerations

- **Managed Identity** eliminates credential management
- **Network isolation** through private endpoints (optional)
- **Audit logging** in Application Insights
- **Role-based access control** for Azure resources
- **SharePoint permissions** restrict file access
- **Container security** with minimal base image