# Azure AD Application Permissions Required for SharePoint Access

## Current Issue
The Azure AD application needs additional permissions to access SharePoint sites and document libraries.

## Required Microsoft Graph API Permissions

### Application Permissions (for service-to-service access):
1. **Sites.ReadWrite.All** - Read and write items in all site collections
2. **Files.ReadWrite.All** - Read and write files in all site collections  
3. **Sites.Read.All** - Read items in all site collections (minimum read permission)

### Delegated Permissions (if using user context):
1. **Sites.ReadWrite.All** - Read and write user's sites
2. **Files.ReadWrite.All** - Read and write user's files

## How to Add These Permissions

### Option 1: Azure Portal
1. Go to Azure Portal > Azure Active Directory > App registrations
2. Find your application (Client ID: 99bfa715-5285-4904-812a-99af4937dab6)
3. Click on "API permissions"
4. Click "Add a permission"
5. Select "Microsoft Graph"
6. Choose "Application permissions" 
7. Find and add:
   - Sites.ReadWrite.All
   - Files.ReadWrite.All
8. Click "Grant admin consent for [Your Organization]"

### Option 2: SharePoint Admin Center
1. Go to SharePoint Admin Center
2. Navigate to "Advanced" > "API access"  
3. Add permissions for your Client ID:
   - Microsoft Graph: Sites.ReadWrite.All
   - Microsoft Graph: Files.ReadWrite.All

### Option 3: Alternative Approach - SharePoint App-Only
Instead of Graph API, we could use SharePoint REST API with app-only permissions:
1. Register app in SharePoint (/_layouts/15/appregnew.aspx)
2. Grant permissions (/_layouts/15/appinv.aspx)
3. Use SharePoint REST endpoints instead of Graph API

## Testing After Permission Changes
After adding permissions and granting admin consent, wait 5-10 minutes for permissions to propagate, then test again with:

```bash
python3 test_sharepoint_connection.py
```

## Alternative: Manual File Management
If permissions are complex to set up, we could:
1. Create a simple file drop zone in SharePoint
2. Use Power Automate to monitor the folder and process TD SYNNEX files
3. Have the service upload files to a different accessible location (Azure Blob Storage, OneDrive, etc.)

## Current Status
- ✅ Azure AD authentication working
- ✅ Site ID retrieval working  
- ❌ Document library access blocked (403 Forbidden)
- ❌ No drives visible (empty drives list)

The application can authenticate and find the site, but cannot access the document libraries due to insufficient permissions.