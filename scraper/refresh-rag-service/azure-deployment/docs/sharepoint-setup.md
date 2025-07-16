# SharePoint Site Setup Guide

This guide walks you through creating the `refresh-synnex-data` SharePoint site for storing ec-synnex files.

## Method 1: PowerShell Script (Recommended)

### Prerequisites
- SharePoint Online Management Shell
- SharePoint Administrator permissions

### Step 1: Install SharePoint Online Management Shell

**On Windows:**
```powershell
Install-Module -Name Microsoft.Online.SharePoint.PowerShell -Force
```

**On macOS:**
```bash
# Install PowerShell first if not installed
brew install --cask powershell

# Then install SharePoint module
pwsh -Command "Install-Module -Name Microsoft.Online.SharePoint.PowerShell -Force"
```

### Step 2: Run SharePoint Creation Script

Save this script as `create-sharepoint-site.ps1`:

```powershell
# SharePoint Site Creation Script
param(
    [Parameter(Mandatory=$true)]
    [string]$TenantUrl,  # e.g., "https://yourtenant-admin.sharepoint.com"
    
    [Parameter(Mandatory=$false)]
    [string]$SiteUrl = "refresh-synnex-data",
    
    [Parameter(Mandatory=$false)]
    [string]$SiteTitle = "Refresh Synnex Data",
    
    [Parameter(Mandatory=$false)]
    [string]$OwnerEmail
)

# Connect to SharePoint Online
Write-Host "Connecting to SharePoint Online..." -ForegroundColor Green
Connect-SPOService -Url $TenantUrl

# Get current user if owner not specified
if (-not $OwnerEmail) {
    $OwnerEmail = (Get-SPOUser -Site $TenantUrl -LoginName (whoami)).LoginName
}

# Create the site
$FullSiteUrl = "$($TenantUrl.Replace('-admin', ''))sites/$SiteUrl"

Write-Host "Creating SharePoint site: $FullSiteUrl" -ForegroundColor Green

try {
    New-SPOSite -Url $FullSiteUrl `
                -Title $SiteTitle `
                -Owner $OwnerEmail `
                -StorageQuota 1000 `
                -Template "STS#3" `
                -NoWait
    
    Write-Host "Site creation initiated successfully!" -ForegroundColor Green
    Write-Host "Site URL: $FullSiteUrl" -ForegroundColor Yellow
    Write-Host "It may take a few minutes for the site to be fully provisioned." -ForegroundColor Yellow
    
    # Wait for site to be ready
    Write-Host "Waiting for site to be ready..." -ForegroundColor Green
    do {
        Start-Sleep -Seconds 30
        $site = Get-SPOSite -Identity $FullSiteUrl -ErrorAction SilentlyContinue
        Write-Host "." -NoNewline
    } while ($site.Status -ne "Active")
    
    Write-Host "`nSite is now active!" -ForegroundColor Green
    
    # Create document library for ec-synnex files
    Write-Host "Creating document library..." -ForegroundColor Green
    
    # Connect to the new site to create library
    $Context = New-Object Microsoft.SharePoint.Client.ClientContext($FullSiteUrl)
    $Context.Credentials = New-Object Microsoft.SharePoint.Client.SharePointOnlineCredentials($OwnerEmail, (ConvertTo-SecureString -String "password" -AsPlainText -Force))
    
    # Create the library
    $Web = $Context.Web
    $ListCreationInfo = New-Object Microsoft.SharePoint.Client.ListCreationInformation
    $ListCreationInfo.Title = "EC Synnex Files"
    $ListCreationInfo.TemplateType = 101  # Document Library
    $List = $Web.Lists.Add($ListCreationInfo)
    $Context.ExecuteQuery()
    
    Write-Host "Document library 'EC Synnex Files' created successfully!" -ForegroundColor Green
    
    # Output important information
    Write-Host "`n=== IMPORTANT INFORMATION ===" -ForegroundColor Cyan
    Write-Host "SharePoint Site URL: $FullSiteUrl" -ForegroundColor Yellow
    Write-Host "Document Library: EC Synnex Files" -ForegroundColor Yellow
    Write-Host "Full Library URL: $FullSiteUrl/EC%20Synnex%20Files" -ForegroundColor Yellow
    Write-Host "`nSave these URLs for the Azure deployment configuration!" -ForegroundColor Red
    
} catch {
    Write-Error "Failed to create SharePoint site: $($_.Exception.Message)"
    exit 1
}

# Disconnect
Disconnect-SPOService
```

### Step 3: Execute the Script

```bash
# Run the PowerShell script
pwsh ./create-sharepoint-site.ps1 -TenantUrl "https://yourtenant-admin.sharepoint.com" -OwnerEmail "your.email@company.com"
```

## Method 2: Web Interface (Manual)

If you prefer to create the site manually through the web interface:

### Step 1: Access SharePoint Admin Center

1. Go to https://admin.microsoft.com
2. Navigate to **Admin centers** → **SharePoint**
3. Click **Sites** → **Active sites**

### Step 2: Create New Site

1. Click **+ Create**
2. Select **Team site**
3. Fill in the details:
   - **Site name**: `Refresh Synnex Data`
   - **Site address**: `refresh-synnex-data`
   - **Description**: `Storage for EC Synnex files for Copilot Studio knowledge refresh`
   - **Language**: English
   - **Privacy settings**: Private (recommended)

### Step 3: Create Document Library

1. Navigate to your new site: `https://yourtenant.sharepoint.com/sites/refresh-synnex-data`
2. Click **+ New** → **Document library**
3. Name: `EC Synnex Files`
4. Description: `Storage for ec-synnex-*.xls files`
5. Click **Create**

### Step 4: Configure Permissions

1. Click **Settings** gear → **Site permissions**
2. Add appropriate users/groups who need to upload files
3. Ensure the Azure Managed Identity will have access (configured later)

## Method 3: Microsoft Graph API (Automated)

For fully automated setup, you can use the Microsoft Graph API:

```bash
# This will be handled by the Azure deployment scripts
./scripts/setup-sharepoint-api.sh
```

## Post-Creation Steps

### 1. Note Important URLs

After creation, save these URLs for the Azure deployment:

```
Site URL: https://yourtenant.sharepoint.com/sites/refresh-synnex-data
Library URL: https://yourtenant.sharepoint.com/sites/refresh-synnex-data/EC%20Synnex%20Files
Site ID: [Will be retrieved by deployment scripts]
Library ID: [Will be retrieved by deployment scripts]
```

### 2. Test File Upload

1. Navigate to the document library
2. Upload a test file (e.g., `test-ec-synnex-sample.xls`)
3. Verify the file appears in the library
4. Delete the test file

### 3. Configure Folder Structure (Optional)

You can create folders to organize files:
- **Current** - For the latest files
- **Archive** - For processed files
- **Failed** - For files that failed processing

## Verification

To verify your SharePoint site is ready:

1. **Site Access**: Can you navigate to the site URL?
2. **Library Access**: Can you see the "EC Synnex Files" library?
3. **Upload Permission**: Can you upload a file?
4. **File Visibility**: Do uploaded files appear immediately?

## Troubleshooting

### Common Issues

**Issue**: "Access Denied" when creating site
**Solution**: Ensure you have SharePoint Administrator permissions

**Issue**: PowerShell module not found
**Solution**: Run `Install-Module Microsoft.Online.SharePoint.PowerShell -Force`

**Issue**: Site creation fails
**Solution**: Check if site name is already taken, try a different name

**Issue**: Can't connect to SharePoint Online
**Solution**: Verify your tenant URL format: `https://yourtenant-admin.sharepoint.com`

### Getting Your Tenant URL

If you don't know your tenant URL:

1. Go to https://admin.microsoft.com
2. Look at the URL, it will be like: `https://admin.microsoft.com/adminportal/tenant/overview#/overview/tenantid/yourtenant`
3. Your tenant name is the part before `.onmicrosoft.com`
4. Your admin URL is: `https://yourtenant-admin.sharepoint.com`
5. Your site URL is: `https://yourtenant.sharepoint.com`

## Next Steps

Once your SharePoint site is created:

1. ✅ Save the site and library URLs
2. ✅ Proceed to the Azure deployment: `docs/deployment-guide.md`
3. ✅ Configure the container to monitor this SharePoint location

The Azure deployment scripts will automatically configure permissions and API access for the managed identity.