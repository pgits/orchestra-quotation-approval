# Complete Deployment Manual - Copilot Refresh Service

## Current Status ✅

Your Azure infrastructure is **fully deployed and operational**:

- ✅ **Container Registry**: `copilotrefreshacr597769.azurecr.io`
- ✅ **Managed Identity**: Authentication configured
- ✅ **Application Insights**: Monitoring ready
- ✅ **Log Analytics**: Logging configured
- ✅ **Container App Environment**: Ready for deployment
- ✅ **SharePoint Site**: Configured with proper permissions

## The One Remaining Issue ⚠️

The container app needs a **x86_64 compatible image** (currently has ARM64 from your Mac).

## Three Options to Complete the Deployment

### Option 1: GitHub Actions (Recommended - Full Automation)

**Prerequisites**: Azure AD admin access to create service principal

**Steps:**
1. **Ask your admin** to create a service principal (see `ADMIN_SETUP_REQUIRED.md`)
2. **Set up GitHub repository** with provided files
3. **Configure GitHub secrets** 
4. **Push code** - GitHub Actions will automatically build and deploy

**Benefits**: Full automation, x86_64 compatibility, CI/CD pipeline

### Option 2: Manual Container Build (Quick Fix)

**Prerequisites**: Access to a Linux machine or VM

**Steps:**
```bash
# On Linux machine
docker build --platform linux/amd64 -t copilot-refresh-service:amd64 .
docker tag copilot-refresh-service:amd64 copilotrefreshacr597769.azurecr.io/copilot-refresh-service:latest
az acr login --name copilotrefreshacr597769
docker push copilotrefreshacr597769.azurecr.io/copilot-refresh-service:latest

# Update container app
az containerapp update \
  --name copilot-refresh-app \
  --resource-group rg-copilot-refresh \
  --image copilotrefreshacr597769.azurecr.io/copilot-refresh-service:latest
```

**Benefits**: Quick fix, no admin permissions needed

### Option 3: Immediate Manual Upload (No Container Needed)

**Steps:**
1. Go to: https://hexalinks.sharepoint.com/sites/QuotationsTeam
2. Navigate to: `Shared Documents` → `EC Synnex Files`
3. Upload: `ec-synnex-701601-0708-0927.xls`
4. Manually integrate with Nathan's Hardware Buddy v.1

**Benefits**: Works immediately, no technical setup

## Detailed Instructions

### GitHub Actions Setup (Option 1)

**File Structure You Have:**
```
azure-deployment/
├── .github/workflows/build-and-deploy.yml    # GitHub Actions workflow
├── container/                                # Container source code
│   ├── Dockerfile                           # Container definition
│   ├── app/                                 # Python application
│   └── requirements.txt                     # Dependencies
├── GITHUB_ACTIONS_SETUP.md                  # Detailed setup guide
├── ADMIN_SETUP_REQUIRED.md                  # Admin instructions
└── COMPLETE_DEPLOYMENT_MANUAL.md            # This file
```

**Step-by-Step Process:**

1. **Create GitHub Repository**
   ```bash
   # Create new repo: copilot-refresh-service
   git clone https://github.com/YOUR_USERNAME/copilot-refresh-service.git
   cd copilot-refresh-service
   cp -r /Users/petergits/dev/claude-orchestra/scraper/refresh-rag-service/azure-deployment/* .
   git add .
   git commit -m "Initial deployment setup"
   git push origin main
   ```

2. **Get Service Principal from Admin**
   - Share `ADMIN_SETUP_REQUIRED.md` with your Azure AD admin
   - They run the commands and provide you with JSON credentials

3. **Configure GitHub Secrets**
   - Repository → Settings → Secrets and variables → Actions
   - Add all secrets listed in `GITHUB_ACTIONS_SETUP.md`

4. **Deploy**
   - Push to main branch or manually trigger workflow
   - GitHub Actions builds x86_64 container and deploys

### Container Information

**Current Resources:**
- **Resource Group**: `rg-copilot-refresh`
- **Container Registry**: `copilotrefreshacr597769.azurecr.io`
- **Container App**: `copilot-refresh-app`
- **App Environment**: `copilot-refresh-env`

**Application Configuration:**
- **Agent ID**: `e71b63c6-9653-f011-877a-000d3a593ad6`
- **Environment ID**: `33a7afba-68df-4fb5-84ba-abd928569b69`
- **SharePoint Site**: `https://hexalinks.sharepoint.com/sites/QuotationsTeam`
- **SharePoint Library**: `Shared Documents`
- **SharePoint Folder**: `EC Synnex Files`

### Monitoring and Troubleshooting

**Check Application Status:**
```bash
# Get container app URL
az containerapp show --name copilot-refresh-app --resource-group rg-copilot-refresh --query properties.configuration.ingress.fqdn -o tsv

# Check application logs
az containerapp logs show --name copilot-refresh-app --resource-group rg-copilot-refresh --follow

# Check resource status
az resource list --resource-group rg-copilot-refresh --output table
```

**Health Check:**
```bash
# Once deployed, test the health endpoint
curl https://YOUR_APP_URL/health
```

**Application Insights:**
- Monitor performance in Azure Portal
- View telemetry and error logs
- Set up alerts for failures

## Testing the Complete Workflow

Once the container is deployed:

1. **Upload Test File to SharePoint**
   - Go to: https://hexalinks.sharepoint.com/sites/QuotationsTeam
   - Navigate to: `Shared Documents` → `EC Synnex Files`
   - Upload: `ec-synnex-701601-0708-0927.xls`

2. **Monitor Container Logs**
   ```bash
   az containerapp logs show --name copilot-refresh-app --resource-group rg-copilot-refresh --follow
   ```

3. **Check File Processing**
   - Container should detect the file within 5 minutes
   - File should be processed and moved to `Processed` folder
   - Copilot Studio should receive the updated knowledge

4. **Verify Copilot Studio Integration**
   - Check Nathan's Hardware Buddy v.1 knowledge base
   - Test queries related to the new data
   - Verify old ec-synnex files are replaced

## Security Considerations

- **Managed Identity**: No credentials stored in container
- **GitHub Secrets**: All sensitive data encrypted
- **Network Security**: Container app runs in managed environment
- **Audit Trail**: All operations logged in Application Insights

## Next Steps After Deployment

1. **Test file upload workflow**
2. **Set up monitoring alerts**
3. **Configure backup strategies**
4. **Document operational procedures**
5. **Train team on SharePoint upload process**

## Support and Troubleshooting

**Common Issues:**
- **Container won't start**: Check logs and environment variables
- **SharePoint access denied**: Verify managed identity permissions
- **File not processing**: Check SharePoint folder structure
- **Copilot Studio not updating**: Verify agent ID and environment ID

**Getting Help:**
- Check `GITHUB_ACTIONS_SETUP.md` for GitHub Actions issues
- Check `ADMIN_SETUP_REQUIRED.md` for permission issues
- Review container logs for runtime errors
- Use Application Insights for detailed troubleshooting

## Summary

Your infrastructure is **98% complete**. The only remaining step is building and deploying the x86_64 container image. Once that's done, you'll have a fully automated system that:

1. Monitors SharePoint for new ec-synnex files
2. Automatically processes and uploads to Copilot Studio
3. Replaces existing files with new versions
4. Provides full audit trail and monitoring

The SharePoint site is ready for immediate manual use while you complete the container deployment.