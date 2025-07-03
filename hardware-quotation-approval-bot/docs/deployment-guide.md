# Hardware Quotation Approval Bot - Deployment Guide

This guide provides step-by-step instructions for deploying the Hardware Quotation Approval Bot to Microsoft Teams using Copilot Studio.

## Prerequisites

Before deploying, ensure you have:

1. **Licenses**
   - Microsoft 365 license with Teams
   - Power Platform license (Power Apps, Power Automate)
   - Copilot Studio license

2. **Permissions**
   - Global Administrator or Application Administrator in Azure AD
   - Environment Maker in Power Platform
   - Teams Administrator

3. **Tools**
   - [Power Platform CLI](https://aka.ms/PowerPlatformCLI)
   - [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) (optional)
   - PowerShell 5.1 or higher
   - Visual Studio Code (recommended)

## Deployment Steps

### Step 1: Prepare Environment

1. **Create Power Platform Environment**
   ```powershell
   # Login to Power Platform
   pac auth create --tenant <your-tenant-id>
   
   # Create new environment (if needed)
   pac admin create --name "QuotationApproval" --type "Production"
   ```

2. **Enable Dataverse**
   - Navigate to [Power Platform Admin Center](https://admin.powerplatform.microsoft.com)
   - Select your environment
   - Ensure Dataverse is enabled

### Step 2: Configure Azure AD Application

1. **Register Application**
   ```bash
   # Using Azure CLI
   az ad app create --display-name "Hardware Quotation Approval Bot" \
     --identifier-uris "api://copilot-studio-quotation-approval" \
     --sign-in-audience "AzureADMyOrg"
   ```

2. **Update Manifest**
   - Navigate to Azure Portal > App registrations
   - Select your app
   - Go to Manifest
   - Replace with content from `/authentication/app-registration-manifest.json`
   - Update placeholder values:
     - `{{APPLICATION_ID}}`
     - `{{CLIENT_ID}}`
     - `{{TENANT_ID}}`
     - Generate new GUIDs for role IDs

3. **Create Client Secret**
   - Go to Certificates & secrets
   - New client secret
   - Save the secret value securely

### Step 3: Deploy Copilot Studio Solution

1. **Run Deployment Script**
   ```powershell
   cd deployment
   
   .\deploy-to-copilot-studio.ps1 `
     -TenantId "<your-tenant-id>" `
     -EnvironmentId "<your-environment-id>" `
     -SolutionName "HardwareQuotationApprovalBot"
   ```

2. **Verify Deployment**
   - Navigate to [Power Apps](https://make.powerapps.com)
   - Select your environment
   - Go to Solutions
   - Verify "HardwareQuotationApprovalBot" is listed

### Step 4: Configure Copilot Studio Bot

1. **Access Copilot Studio**
   - Go to [Copilot Studio](https://web.powerva.microsoft.com)
   - Select your environment
   - Find "Hardware Quotation Approval Bot"

2. **Configure Authentication**
   - Go to Settings > Security > Authentication
   - Select "Manual (for any channel)"
   - Enter Azure AD details:
     - Client ID
     - Client Secret
     - Tenant ID
     - Scopes: `api://copilot-studio-quotation-approval/access_as_user`

3. **Configure Channels**
   - Go to Channels
   - Select Microsoft Teams
   - Click "Turn on Teams"

### Step 5: Deploy to Teams

1. **Prepare Teams App Package**
   - Update `/authentication/teams-app-manifest.json` with actual values:
     - `{{TEAMS_APP_ID}}` - Generate new GUID
     - `{{BOT_ID}}` - From Copilot Studio bot settings
     - `{{CLIENT_ID}}` - From Azure AD app
   
2. **Create App Package**
   ```powershell
   # Create icons if not exists
   mkdir icons
   # Add 192x192 color.png and 32x32 outline.png
   
   # Create zip package
   Compress-Archive -Path @(
     "authentication/teams-app-manifest.json",
     "icons/color.png",
     "icons/outline.png"
   ) -DestinationPath "teams-app.zip"
   ```

3. **Upload to Teams Admin Center**
   - Go to [Teams Admin Center](https://admin.teams.microsoft.com)
   - Teams apps > Manage apps
   - Upload > Upload app package
   - Select your zip file

4. **Set App Policies**
   - Go to Teams apps > Setup policies
   - Add app to relevant policies
   - Assign to users/groups

### Step 6: Configure Dataverse

1. **Set Up Approval Limits**
   ```sql
   -- Example data for approval limits
   INSERT INTO cr_approvallimit (cr_role, cr_minamount, cr_maxamount, cr_hierarchylevel)
   VALUES 
   ('Team Member', 0, 1000, 1),
   ('Team Lead', 0, 5000, 2),
   ('Manager', 0, 25000, 3),
   ('Director', 0, 100000, 4),
   ('VP', 0, 500000, 5);
   ```

2. **Configure Security Roles**
   - Navigate to Power Platform Admin Center
   - Select environment > Settings > Security > Security roles
   - Create/modify roles for approval levels

### Step 7: Test Deployment

1. **Test in Teams**
   - Open Microsoft Teams
   - Search for "HW Quotation Approval"
   - Start conversation
   - Send test message

2. **Test Integration**
   ```json
   // Test webhook payload
   POST https://your-environment.crm.dynamics.com/api/quotation-approval/trigger
   {
     "quotationId": "QT-000001",
     "customerName": "Test Customer",
     "hardwareDetails": {
       "items": [{
         "name": "Test Laptop",
         "quantity": 1,
         "unitPrice": 999.99
       }],
       "justification": "Testing deployment"
     },
     "totalAmount": 999.99,
     "requesterId": "user@company.com",
     "callbackUrl": "https://webhook.site/test"
   }
   ```

### Step 8: Production Configuration

1. **Environment Variables**
   - Go to Power Apps > Solutions > Your solution
   - Add environment variables for:
     - API endpoints
     - Authentication settings
     - Feature flags

2. **Monitoring Setup**
   - Enable Application Insights
   - Configure Power Platform analytics
   - Set up alert rules

3. **Backup Strategy**
   - Export solution regularly
   - Document customizations
   - Version control integration files

## Troubleshooting

### Common Issues

1. **Bot not responding in Teams**
   - Check bot endpoint in Copilot Studio
   - Verify Teams channel is enabled
   - Check authentication configuration

2. **Authentication errors**
   - Verify Azure AD app permissions
   - Check client secret hasn't expired
   - Ensure redirect URIs are correct

3. **Dataverse errors**
   - Check user has correct security role
   - Verify entity permissions
   - Check field-level security

### Debug Commands

```powershell
# Check solution import status
pac solution list

# Verify bot registration
pac pva list

# Test Power Automate flows
pac flow list

# Check Dataverse entities
pac data list
```

## Maintenance

### Regular Tasks

1. **Weekly**
   - Review approval metrics
   - Check failed callbacks
   - Monitor error logs

2. **Monthly**
   - Update approval limits
   - Review user access
   - Performance optimization

3. **Quarterly**
   - Security audit
   - License review
   - Feature updates

### Updating the Bot

1. **Export Current Solution**
   ```powershell
   pac solution export --path backup.zip --name HardwareQuotationApprovalBot
   ```

2. **Make Changes**
   - Update topics in Copilot Studio
   - Modify flows in Power Automate
   - Update Dataverse schema

3. **Import Updated Solution**
   ```powershell
   pac solution import --path updated.zip --force-overwrite
   ```

## Support

For issues or questions:
1. Check [Microsoft Copilot Studio documentation](https://docs.microsoft.com/en-us/power-virtual-agents/)
2. Review [Power Platform community](https://powerusers.microsoft.com/)
3. Contact your IT administrator

## Appendix

### Useful PowerShell Commands

```powershell
# Get environment details
pac env list

# Check solution components
pac solution list-component --solution-name HardwareQuotationApprovalBot

# Export solution for backup
pac solution export --path "backup-$(Get-Date -Format 'yyyyMMdd').zip"

# Check bot health
pac pva list --environment-id <env-id>
```

### API Reference

See `/integration/webhook-endpoint.json` for complete API documentation.

### Security Considerations

1. Always use HTTPS for callbacks
2. Implement rate limiting
3. Regular security audits
4. Monitor for suspicious activity
5. Keep secrets in Key Vault

---

Last updated: {{CURRENT_DATE}}