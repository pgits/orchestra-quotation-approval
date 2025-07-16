# Get Copilot Studio Agent ID by name
# This script helps you find the Agent ID for your Copilot Studio agent

param(
    [Parameter(Mandatory=$true)]
    [string]$AgentName,
    
    [Parameter(Mandatory=$false)]
    [string]$EnvironmentId
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

# Set environment if provided
if ($EnvironmentId) {
    Write-Host "Setting target environment: $EnvironmentId"
    pac org select --environment $EnvironmentId
}

Write-Host "Searching for Copilot Studio agent: $AgentName"

# List all copilots in the environment
$copilotList = pac copilot list --json | ConvertFrom-Json

if ($copilotList.Count -eq 0) {
    Write-Warning "No copilots found in the current environment."
    exit 0
}

# Find the agent by name
$targetAgent = $copilotList | Where-Object { $_.DisplayName -eq $AgentName -or $_.Name -eq $AgentName }

if ($targetAgent) {
    Write-Host "
=== AGENT FOUND ===
Display Name: $($targetAgent.DisplayName)
Schema Name: $($targetAgent.Name)
Agent ID: $($targetAgent.Id)
Environment: $($targetAgent.EnvironmentId)
State: $($targetAgent.State)
Created: $($targetAgent.CreatedOn)
Modified: $($targetAgent.ModifiedOn)

=== NEXT STEPS ===
1. Copy the Agent ID: $($targetAgent.Id)
2. Update config.json with this ID
3. Run the deploy-flow.ps1 script
"
    
    # Update config.json if it exists
    $configPath = Join-Path $PSScriptRoot "..\config\config.json"
    if (Test-Path $configPath) {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        $config.copilotStudio.agentId = $targetAgent.Id
        $config.copilotStudio.environment.id = $targetAgent.EnvironmentId
        $config | ConvertTo-Json -Depth 5 | Out-File $configPath -Encoding UTF8
        Write-Host "Config.json updated with Agent ID: $($targetAgent.Id)"
    }
    
} else {
    Write-Warning "Agent '$AgentName' not found in the current environment."
    Write-Host "Available agents:"
    $copilotList | Select-Object DisplayName, Name, Id | Format-Table -AutoSize
}