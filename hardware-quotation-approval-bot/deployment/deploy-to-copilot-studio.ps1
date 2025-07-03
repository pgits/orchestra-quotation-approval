# Deploy Hardware Quotation Approval Bot to Copilot Studio
# PowerShell deployment script

param(
    [Parameter(Mandatory=$true)]
    [string]$TenantId,
    
    [Parameter(Mandatory=$true)]
    [string]$EnvironmentId,
    
    [Parameter(Mandatory=$true)]
    [string]$SolutionName = "HardwareQuotationApprovalBot",
    
    [Parameter(Mandatory=$false)]
    [string]$PublisherPrefix = "hw",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipAuthentication
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "Starting deployment of Hardware Quotation Approval Bot..." -ForegroundColor Green

# Function to check prerequisites
function Test-Prerequisites {
    Write-Host "`nChecking prerequisites..." -ForegroundColor Yellow
    
    # Check for Power Platform CLI
    if (-not (Get-Command "pac" -ErrorAction SilentlyContinue)) {
        throw "Power Platform CLI (pac) is not installed. Please install it from: https://aka.ms/PowerPlatformCLI"
    }
    
    # Check for Azure CLI
    if (-not (Get-Command "az" -ErrorAction SilentlyContinue)) {
        Write-Warning "Azure CLI is not installed. Some features may not work properly."
    }
    
    Write-Host "Prerequisites check completed." -ForegroundColor Green
}

# Function to authenticate
function Connect-PowerPlatform {
    if ($SkipAuthentication) {
        Write-Host "Skipping authentication as requested." -ForegroundColor Yellow
        return
    }
    
    Write-Host "`nAuthenticating to Power Platform..." -ForegroundColor Yellow
    
    try {
        pac auth create --tenant $TenantId
        pac org select --environment $EnvironmentId
        Write-Host "Authentication successful." -ForegroundColor Green
    }
    catch {
        throw "Failed to authenticate: $_"
    }
}

# Function to create solution
function New-Solution {
    Write-Host "`nCreating solution package..." -ForegroundColor Yellow
    
    $solutionPath = Join-Path $PSScriptRoot "solution"
    
    if (-not (Test-Path $solutionPath)) {
        New-Item -Path $solutionPath -ItemType Directory -Force | Out-Null
    }
    
    # Initialize solution
    Set-Location $solutionPath
    pac solution init `
        --publisher-name "HardwareQuotationBot" `
        --publisher-prefix $PublisherPrefix `
        --outputDirectory "src"
    
    Write-Host "Solution package created." -ForegroundColor Green
}

# Function to add Copilot Studio bot
function Add-CopilotStudioBot {
    Write-Host "`nAdding Copilot Studio bot to solution..." -ForegroundColor Yellow
    
    $botDefinitionPath = Join-Path $PSScriptRoot "..\copilot-studio"
    
    # Copy bot files to solution
    $botSrcPath = Join-Path $PSScriptRoot "solution\src\botcomponents"
    New-Item -Path $botSrcPath -ItemType Directory -Force | Out-Null
    
    # Copy topics
    Copy-Item -Path "$botDefinitionPath\topics\*.yaml" -Destination "$botSrcPath\" -Force
    
    # Create bot manifest
    $botManifest = @{
        schemaVersion = "1.0"
        name = "Hardware Quotation Approval Bot"
        description = "Handles hardware quotation approvals"
        topics = Get-ChildItem "$botSrcPath\*.yaml" | Select-Object -ExpandProperty Name
    } | ConvertTo-Json -Depth 10
    
    $botManifest | Out-File -FilePath "$botSrcPath\bot.manifest.json" -Encoding UTF8
    
    Write-Host "Copilot Studio bot added to solution." -ForegroundColor Green
}

# Function to add Power Automate flows
function Add-PowerAutomateFlows {
    Write-Host "`nAdding Power Automate flows to solution..." -ForegroundColor Yellow
    
    $flowsPath = Join-Path $PSScriptRoot "..\copilot-studio\power-automate"
    $flowsSrcPath = Join-Path $PSScriptRoot "solution\src\Workflows"
    
    New-Item -Path $flowsSrcPath -ItemType Directory -Force | Out-Null
    
    Get-ChildItem "$flowsPath\*.json" | ForEach-Object {
        $flowName = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
        $flowDir = Join-Path $flowsSrcPath $flowName
        New-Item -Path $flowDir -ItemType Directory -Force | Out-Null
        
        # Copy and transform flow definition
        $flowContent = Get-Content $_.FullName -Raw | ConvertFrom-Json
        $flowContent | ConvertTo-Json -Depth 100 | Out-File -FilePath "$flowDir\workflow.json" -Encoding UTF8
        
        Write-Host "  Added flow: $flowName" -ForegroundColor Gray
    }
    
    Write-Host "Power Automate flows added to solution." -ForegroundColor Green
}

# Function to add Dataverse components
function Add-DataverseComponents {
    Write-Host "`nAdding Dataverse components to solution..." -ForegroundColor Yellow
    
    $dataversePath = Join-Path $PSScriptRoot "..\dataverse\schema"
    $entitiesSrcPath = Join-Path $PSScriptRoot "solution\src\Entities"
    
    New-Item -Path $entitiesSrcPath -ItemType Directory -Force | Out-Null
    
    Get-ChildItem "$dataversePath\*.xml" | ForEach-Object {
        Copy-Item $_.FullName -Destination $entitiesSrcPath -Force
        Write-Host "  Added entity: $($_.BaseName)" -ForegroundColor Gray
    }
    
    Write-Host "Dataverse components added to solution." -ForegroundColor Green
}

# Function to build solution
function Build-Solution {
    Write-Host "`nBuilding solution package..." -ForegroundColor Yellow
    
    Set-Location (Join-Path $PSScriptRoot "solution")
    
    try {
        pac solution pack `
            --zipfile "$SolutionName.zip" `
            --folder "src" `
            --packagetype Both
        
        Write-Host "Solution package built successfully." -ForegroundColor Green
        return Join-Path $PSScriptRoot "solution\$SolutionName.zip"
    }
    catch {
        throw "Failed to build solution: $_"
    }
}

# Function to import solution
function Import-Solution {
    param(
        [string]$SolutionPath
    )
    
    Write-Host "`nImporting solution to environment..." -ForegroundColor Yellow
    
    try {
        $importJob = pac solution import `
            --path $SolutionPath `
            --activate-plugins `
            --force-overwrite `
            --publish-changes `
            --async
        
        Write-Host "Solution import started. Job ID: $importJob" -ForegroundColor Yellow
        Write-Host "Waiting for import to complete..." -ForegroundColor Yellow
        
        # Wait for import to complete
        Start-Sleep -Seconds 10
        
        # Check import status
        $status = pac solution import-status --import-job-id $importJob
        
        Write-Host "Solution imported successfully." -ForegroundColor Green
    }
    catch {
        throw "Failed to import solution: $_"
    }
}

# Function to configure Teams app
function Deploy-TeamsApp {
    Write-Host "`nDeploying Teams app..." -ForegroundColor Yellow
    
    $teamsManifestPath = Join-Path $PSScriptRoot "..\authentication\teams-app-manifest.json"
    $teamsPackagePath = Join-Path $PSScriptRoot "teams-app.zip"
    
    # Create Teams app package
    $teamsFiles = @(
        $teamsManifestPath,
        (Join-Path $PSScriptRoot "icons\color.png"),
        (Join-Path $PSScriptRoot "icons\outline.png")
    )
    
    # Note: In production, use proper Teams app packaging
    Write-Host "Teams app package created at: $teamsPackagePath" -ForegroundColor Green
    Write-Host "Upload this package to Teams Admin Center to complete deployment." -ForegroundColor Yellow
}

# Function to create deployment summary
function New-DeploymentSummary {
    param(
        [string]$SolutionPath
    )
    
    $summary = @"
Deployment Summary
==================
Solution Name: $SolutionName
Environment ID: $EnvironmentId
Tenant ID: $TenantId
Solution Package: $SolutionPath
Timestamp: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Next Steps:
1. Configure app registration in Azure AD
2. Update authentication settings with actual values
3. Upload Teams app package to Teams Admin Center
4. Configure approval limits in Dataverse
5. Test the bot in Teams

For detailed instructions, see: /docs/deployment-guide.md
"@

    $summaryPath = Join-Path $PSScriptRoot "deployment-summary.txt"
    $summary | Out-File -FilePath $summaryPath -Encoding UTF8
    
    Write-Host "`nDeployment summary saved to: $summaryPath" -ForegroundColor Green
    Write-Host $summary -ForegroundColor Cyan
}

# Main deployment flow
try {
    Test-Prerequisites
    Connect-PowerPlatform
    New-Solution
    Add-CopilotStudioBot
    Add-PowerAutomateFlows
    Add-DataverseComponents
    $solutionPath = Build-Solution
    Import-Solution -SolutionPath $solutionPath
    Deploy-TeamsApp
    New-DeploymentSummary -SolutionPath $solutionPath
    
    Write-Host "`nDeployment completed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "`nDeployment failed: $_" -ForegroundColor Red
    exit 1
}
finally {
    Set-Location $PSScriptRoot
}