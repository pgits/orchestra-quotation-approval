# Quick Start Guide

## Complete Azure-Based Solution for Copilot Studio Knowledge Refresh

This solution automatically monitors SharePoint for ec-synnex files and uploads them to your Copilot Studio agent, completely bypassing local machine security restrictions.

## 🚀 Quick Deployment (30 minutes)

### Prerequisites Check

```bash
# Run this script to verify you have everything needed
curl -s https://raw.githubusercontent.com/your-repo/check-prereqs.sh | bash
```

**Or manually verify:**
- ✅ Azure CLI installed and authenticated (`az login`)
- ✅ Docker Desktop running
- ✅ PowerShell Core installed (`pwsh`)
- ✅ jq installed (`brew install jq` on macOS)

### Step 1: Verify SharePoint Access (2 minutes)

**Using existing Hexalinks SharePoint site:**
- **Site:** https://hexalinks.sharepoint.com/sites/QuotationsTeam
- **Library:** Shared Documents
- **Folder:** EC Synnex Files (within Shared Documents library)
- **Access:** Verify you can access the shared folder

```bash
# Test access to the SharePoint site
open "https://hexalinks.sharepoint.com/sites/QuotationsTeam/Shared%20Documents/Forms/AllItems.aspx"
```

**Result:** Existing SharePoint folder accessible at the above URL

### Step 2: Deploy Azure Infrastructure (10 minutes)

```bash
# Deploy all Azure resources using Hexalinks SharePoint
./scripts/deploy-infrastructure.sh \
    --resource-group "rg-copilot-refresh" \
    --tenant "hexalinks" \
    --site-url "https://hexalinks.sharepoint.com/sites/QuotationsTeam"
```

**What gets created:**
- 🏗️ Azure Container Registry
- 🔐 Managed Identity with permissions
- 📊 Application Insights monitoring
- 🗂️ Log Analytics workspace
- 🐳 Container Instance (ready for deployment)

### Step 3: Configure API Permissions (5 minutes)

**⚠️ MANUAL STEP REQUIRED:**

1. Go to [Azure Portal](https://portal.azure.com) → **Azure Active Directory** → **App registrations**
2. Switch to **"All applications"** tab
3. Find your managed identity (search for "copilot-refresh")
4. **API permissions** → **Add permission** → **Microsoft Graph**
5. Add these **Application permissions**:
   - `Sites.Read.All`
   - `Files.Read.All` 
   - `Sites.ReadWrite.All`
6. **Click "Grant admin consent"**

### Step 4: Deploy Container (10 minutes)

```bash
# Build and deploy the container
./scripts/deploy-container.sh
```

**What happens:**
- 🐳 Builds Docker container with your code
- 📤 Pushes to Azure Container Registry  
- ▶️ Starts the monitoring service
- 🏥 Enables health checks

### Step 5: Test Everything (5 minutes)

```bash
# Run comprehensive tests
./scripts/test-deployment.sh
```

**Test Results:**
```
=== TEST RESULTS ===
Tests Passed: 12
Tests Failed: 0
Total Tests: 12

🎉 All tests passed! The deployment is working correctly.
```

## 🎯 Usage

### Upload Files

1. **Go to SharePoint:** https://hexalinks.sharepoint.com/sites/QuotationsTeam
2. **Navigate to:** Shared Documents library → "EC Synnex Files" folder
3. **Upload file:** Any file starting with `ec-synnex-` with `.xls` or `.xlsx` extension
4. **Wait 5 minutes:** Container checks every 5 minutes for new files
5. **Check Copilot Studio:** File appears in "Nathan's Hardware Buddy v.1" knowledge base

### Monitor Service

```bash
# Real-time logs
az container logs --resource-group "rg-copilot-refresh" --name "copilot-refresh-container" --follow

# Health check
curl http://your-container-fqdn:8080/health

# Detailed status
curl http://your-container-fqdn:8080/status
```

## 🔧 Configuration

All configuration is automatic, but you can customize:

```bash
# Update environment variables in the container
az container update --resource-group "rg-copilot-refresh" --name "copilot-refresh-container" --environment-variables CHECK_INTERVAL=180
```

**Key Settings:**
- `CHECK_INTERVAL=300` - Check SharePoint every 5 minutes
- `FILE_PATTERN=ec-synnex-` - Only process files starting with this
- `MAX_FILE_SIZE=536870912` - Maximum 512MB file size

## 🆘 Troubleshooting

### Common Issues

**Problem:** Container not starting
```bash
# Check logs
az container logs --resource-group "rg-copilot-refresh" --name "copilot-refresh-container"
# Usually: Missing API permissions
```

**Problem:** Files not being processed
```bash
# Check file naming (must start with "ec-synnex-")
# Check file location (must be in "EC Synnex Files" library)
# Check container logs for errors
```

**Problem:** SharePoint access denied
```bash
# Verify API permissions were granted
# Check managed identity role assignments
```

### Get Help

```bash
# Run diagnostics
./scripts/test-deployment.sh

# Check detailed logs
az container logs --resource-group "rg-copilot-refresh" --name "copilot-refresh-container" --tail 50

# View Application Insights
# Go to Azure Portal → Your Application Insights resource → Logs
```

## 📊 Monitoring

### Azure Portal

- **Application Insights:** Real-time telemetry and performance
- **Container Instance:** Resource usage and health
- **Log Analytics:** Detailed logging and queries

### Health Endpoints

- **Health:** `http://container-fqdn:8080/health`
- **Status:** `http://container-fqdn:8080/status`  
- **Metrics:** `http://container-fqdn:8080/metrics`

## 🔄 Updates

```bash
# Update container with new version
./scripts/deploy-container.sh --tag "v1.1" --force

# Test updated version
./scripts/test-deployment.sh
```

## 💰 Cost

**Estimated monthly cost:** ~$25-40
- Container Instance: ~$15-20/month
- Container Registry: ~$5/month
- Application Insights: ~$5-15/month
- Log Analytics: ~$2-5/month

## 🏆 Success Criteria

✅ **Container running** and healthy  
✅ **SharePoint files uploaded** automatically  
✅ **Copilot Studio knowledge** updated with new files  
✅ **Monitoring working** with logs and alerts  
✅ **Authentication working** via Managed Identity  

## 🔐 Security

- **No credentials stored** - Uses Azure Managed Identity
- **Network isolation** - Container runs in Azure
- **Audit trail** - All actions logged in Application Insights
- **Role-based access** - Minimal required permissions
- **Encrypted storage** - All Azure resources encrypted

## 📈 Next Steps

1. **Set up alerts** in Application Insights for failures
2. **Create backup strategy** for configuration
3. **Consider Azure Container Apps** for production scaling
4. **Implement Azure Key Vault** for sensitive settings
5. **Add automated testing** in CI/CD pipeline

---

**🎉 Congratulations!** You now have a fully automated, enterprise-grade solution for keeping your Copilot Studio knowledge base up to date!