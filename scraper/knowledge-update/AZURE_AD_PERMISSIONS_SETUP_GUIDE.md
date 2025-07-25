# Azure AD Application Permissions Setup Guide

## Overview
This guide provides detailed steps to add SharePoint permissions to your Azure AD application so the TD SYNNEX knowledge update service can upload files to SharePoint.

**Your Application Details:**
- **Application Name**: TD SYNNEX Knowledge Update Service (or similar)
- **Client ID**: `99bfa715-5285-4904-812a-99af4937dab6`
- **Tenant ID**: `33a7afba-68df-4fb5-84ba-abd928569b69`

## Method 1: Azure Portal (Recommended)

### Step 1: Access Azure Portal
1. Go to [https://portal.azure.com](https://portal.azure.com)
2. Sign in with your admin account that has permissions to manage Azure AD applications
3. Ensure you're in the correct tenant (Hexalinks)

### Step 2: Navigate to App Registrations
1. In the Azure Portal, click on **"Azure Active Directory"** in the left menu
2. Click on **"App registrations"** in the left sidebar
3. Look for your application in the list, or use the search box to find Client ID: `99bfa715-5285-4904-812a-99af4937dab6`
4. Click on the application name to open it

### Step 3: Add API Permissions
1. In your application's overview page, click **"API permissions"** in the left sidebar
2. You should see existing permissions (likely Microsoft Graph permissions for email)
3. Click **"Add a permission"** button

### Step 4: Select Microsoft Graph
1. In the "Request API permissions" panel, click **"Microsoft Graph"**
2. Choose **"Application permissions"** (not Delegated permissions)
   - Application permissions allow the service to run without a user signed in
   - This is what we need for automated file uploads

### Step 5: Add SharePoint Permissions
1. In the search box, type **"Sites"** and look for:
   - ☑️ **Sites.Read.All** - Read items in all site collections
   - ☑️ **Sites.ReadWrite.All** - Read and write items in all site collections
2. Select **Sites.ReadWrite.All** (this includes Sites.Read.All)
3. Click **"Add permissions"**

### Step 6: Add Files Permissions
1. Click **"Add a permission"** again
2. Select **"Microsoft Graph"** → **"Application permissions"**
3. In the search box, type **"Files"** and look for:
   - ☑️ **Files.Read.All** - Read all files
   - ☑️ **Files.ReadWrite.All** - Read and write all files
4. Select **Files.ReadWrite.All**
5. Click **"Add permissions"**

### Step 7: Grant Admin Consent (CRITICAL)
1. Back in the "API permissions" page, you should now see:
   ```
   Microsoft Graph (3-4 permissions)
   ├── Sites.ReadWrite.All - Not granted
   ├── Files.ReadWrite.All - Not granted  
   ├── [existing email permissions] - Granted
   ```
2. Click the **"Grant admin consent for [Your Organization Name]"** button
3. A popup will appear asking for confirmation - click **"Yes"**
4. Wait for the status to change from "Not granted" to "Granted for [Your Org]"
   - This may take 30-60 seconds
5. You should see green checkmarks next to the new permissions

### Step 8: Verify Permissions
Your final permissions list should include:
- ✅ **Microsoft Graph - Sites.ReadWrite.All** - Granted
- ✅ **Microsoft Graph - Files.ReadWrite.All** - Granted  
- ✅ **Microsoft Graph - Mail.Read** - Granted (existing)
- ✅ **Microsoft Graph - User.Read** - Granted (existing)

## Method 2: PowerShell (Alternative for IT Admins)

If you prefer PowerShell or have restrictions in the Azure Portal:

```powershell
# Install required modules if not already installed
Install-Module AzureAD
Install-Module Microsoft.Graph

# Connect to Azure AD
Connect-AzureAD -TenantId "33a7afba-68df-4fb5-84ba-abd928569b69"

# Get your application
$app = Get-AzureADApplication -Filter "AppId eq '99bfa715-5285-4904-812a-99af4937dab6'"

# Get Microsoft Graph service principal
$graphServicePrincipal = Get-AzureADServicePrincipal -Filter "AppId eq '00000003-0000-0000-c000-000000000000'"

# Find the required permissions
$sitesReadWriteAll = $graphServicePrincipal.AppRoles | Where-Object {$_.Value -eq "Sites.ReadWrite.All"}
$filesReadWriteAll = $graphServicePrincipal.AppRoles | Where-Object {$_.Value -eq "Files.ReadWrite.All"}

# Add the permissions
New-AzureADServiceAppRoleAssignment -ObjectId $app.ObjectId -PrincipalId $app.ObjectId -ResourceId $graphServicePrincipal.ObjectId -Id $sitesReadWriteAll.Id
New-AzureADServiceAppRoleAssignment -ObjectId $app.ObjectId -PrincipalId $app.ObjectId -ResourceId $graphServicePrincipal.ObjectId -Id $filesReadWriteAll.Id
```

## Method 3: Azure CLI (Alternative)

```bash
# Login to Azure
az login --tenant 33a7afba-68df-4fb5-84ba-abd928569b69

# Add the required permissions
az ad app permission add --id 99bfa715-5285-4904-812a-99af4937dab6 --api 00000003-0000-0000-c000-000000000000 --api-permissions 332a536c-c7ef-4017-ab91-336970924f0d=Role

az ad app permission add --id 99bfa715-5285-4904-812a-99af4937dab6 --api 00000003-0000-0000-c000-000000000000 --api-permissions 75359482-378d-4052-8f01-80520e7db3cd=Role

# Grant admin consent
az ad app permission admin-consent --id 99bfa715-5285-4904-812a-99af4937dab6
```

## After Adding Permissions

### 1. Wait for Propagation
- Permissions can take **5-15 minutes** to propagate across Microsoft's systems
- Don't test immediately after granting consent

### 2. Test the Connection
```bash
cd /Users/petergits/dev/claude-orchestra/scraper/knowledge-update
python3 test_sharepoint_connection.py
```

**Expected Success Output:**
```
🧪 Testing SharePoint Connection...
✅ SharePoint connection successful!
📋 Listing existing TD SYNNEX files...
Found 0 existing files:
⬆️ Testing file upload...
✅ Test file uploaded successfully!
🧹 Cleaning up test file...
✅ Test file cleaned up successfully!
🎉 All SharePoint tests passed!
```

### 3. Test the Full Service
```bash
# Start the service
python3 app.py

# In another terminal, test the endpoints
curl http://localhost:5000/health
curl http://localhost:5000/sharepoint-files
```

## Troubleshooting Common Issues

### Issue 1: "Access Denied" or 403 Errors
**Solution**: Make sure admin consent was granted properly
- Go back to Azure Portal > App registrations > Your app > API permissions  
- Look for green checkmarks next to permissions
- If not granted, click "Grant admin consent" again

### Issue 2: "Application Not Found"
**Solution**: Verify you're in the correct Azure AD tenant
- Check the tenant ID in the Azure Portal top-right corner
- Should match: `33a7afba-68df-4fb5-84ba-abd928569b69`

### Issue 3: "Insufficient Privileges"
**Solution**: Your account needs to be:
- Global Administrator, or
- Application Administrator, or  
- Cloud Application Administrator

### Issue 4: Permissions Take Too Long to Propagate
**Solution**: Wait longer or try:
- Clear browser cache and re-authenticate
- Wait 30 minutes and test again
- Restart the application service

## Security Considerations

### Principle of Least Privilege
- ✅ We're only requesting permissions needed for SharePoint file operations
- ✅ Using Application permissions (not user permissions) for service accounts
- ✅ Scoped to specific SharePoint site when possible

### Permission Scope
- **Sites.ReadWrite.All**: Allows access to ALL SharePoint sites in your tenant
- **Files.ReadWrite.All**: Allows access to ALL files in your tenant
- Consider using **Sites.Selected** if available (requires additional setup)

### Monitoring
- Monitor the application's activity in Azure AD sign-in logs
- Set up alerts for unusual file access patterns
- Regularly review granted permissions

## Next Steps After Permissions Are Added

1. ✅ Test SharePoint connection
2. ✅ Test TD SYNNEX file upload workflow  
3. ✅ Verify Copilot Studio can access files in SharePoint
4. 🚀 Deploy to Azure containers
5. 📧 Set up automated email monitoring

The service will then automatically:
- Monitor emails for new TD SYNNEX price files
- Process and upload them to SharePoint
- Allow "Nate's Hardware Buddy v.1" to access the latest pricing data