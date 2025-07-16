# Deploy Copilot Knowledge Refresh Flow to Power Automate
# Prerequisites: Install Power Platform CLI and authenticate

param(
    [Parameter(Mandatory=$true)]
    [string]$EnvironmentId,
    
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$false)]
    [string]$FlowName = "Copilot-Knowledge-Refresh-Flow"
)

# Check if Power Platform CLI is installed
if (-not (Get-Command "pac" -ErrorAction SilentlyContinue)) {
    Write-Error "Power Platform CLI is not installed. Please install it first."
    exit 1
}

# Check authentication
$authList = pac auth list
if ($authList -notmatch "Active") {
    Write-Error "Not authenticated to Power Platform. Please run 'pac auth create' first."
    exit 1
}

# Set the target environment
Write-Host "Setting target environment: $EnvironmentId"
pac org select --environment $EnvironmentId

# Import the flow definition
$flowPath = Join-Path $PSScriptRoot "..\flows\copilot-knowledge-refresh-flow.json"
if (-not (Test-Path $flowPath)) {
    Write-Error "Flow definition file not found at: $flowPath"
    exit 1
}

# Create the flow using Azure CLI (as pac doesn't directly support flow import)
Write-Host "Creating Power Automate flow..."

# Read the flow definition
$flowDefinition = Get-Content $flowPath -Raw | ConvertFrom-Json

# Update connection references with actual values
$flowDefinition.parameters.'$connections'.value.shared_commondataservice.connectionId = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.Web/connections/shared_commondataservice"
$flowDefinition.parameters.'$connections'.value.shared_onedriveforbusiness.connectionId = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.Web/connections/shared_onedriveforbusiness"

# Save updated flow definition
$updatedFlowPath = Join-Path $PSScriptRoot "..\flows\copilot-knowledge-refresh-flow-updated.json"
$flowDefinition | ConvertTo-Json -Depth 20 | Out-File $updatedFlowPath -Encoding UTF8

Write-Host "Flow definition updated with connection references"
Write-Host "Flow file saved to: $updatedFlowPath"

# Instructions for manual deployment
Write-Host "
=== MANUAL DEPLOYMENT STEPS ===

1. Open Power Automate portal: https://powerautomate.microsoft.com
2. Navigate to your environment: $EnvironmentId
3. Click 'My flows' > 'Import' > 'Import Package (Legacy)'
4. Upload the flow definition file: $updatedFlowPath
5. Configure the following connections:
   - Dataverse: Connect to your Dataverse environment
   - OneDrive for Business: Connect to your OneDrive account
6. Set the CopilotStudioAgentId parameter to your agent's ID
7. Save and test the flow

=== GETTING AGENT ID ===
Run: Get-CopilotStudioAgentId.ps1 -AgentName 'Nathan's Hardware Buddy v.1'
"

Write-Host "Deployment preparation completed successfully!"