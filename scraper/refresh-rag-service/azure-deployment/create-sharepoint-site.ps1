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
