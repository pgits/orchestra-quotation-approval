# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a Microsoft Teams Copilot Studio agent for hardware quotation approvals. The bot receives approval requests from a parent Copilot Studio agent and handles the approval workflow with role-based limits and comprehensive audit trails.

## Key Commands

### Development
```bash
# Install dependencies (if Node.js project components are added)
npm install

# Deploy to Copilot Studio
npm run deploy
# Or directly:
powershell -ExecutionPolicy Bypass -File ./hardware-quotation-approval-bot/deployment/deploy-to-copilot-studio.ps1 -TenantId "<tenant-id>" -EnvironmentId "<env-id>"

# Validate configuration files
npm run validate

# Run linting on JavaScript files
npm run lint
```

### Power Platform CLI Commands
```bash
# Authenticate to Power Platform
pac auth create --tenant <tenant-id>

# Select environment
pac org select --environment <environment-id>

# List solutions
pac solution list

# Export solution for backup
pac solution export --path backup.zip --name HardwareQuotationApprovalBot

# Import solution
pac solution import --path solution.zip --force-overwrite
```

## Architecture

### High-Level Components

1. **Copilot Studio Bot** (`/copilot-studio/topics/`)
   - Entry point: `main-approval-flow.yaml` - Receives external triggers with quotation data
   - Three decision branches: Approve, Reject, Request More Info
   - Each branch has dedicated topic files for handling specific workflows

2. **Power Automate Flows** (`/copilot-studio/power-automate/`)
   - `log-approval-decision.json` - Persists decisions to Dataverse
   - `send-callback-notification.json` - Notifies parent agent with retry logic
   - `send-teams-notification.json` - Sends rich cards to requesters
   - `check-approval-limits.json` - Validates approver authority based on role

3. **Integration Layer** (`/integration/`)
   - Webhook endpoint configuration for receiving requests
   - Callback handler with exponential backoff retry mechanism
   - Dead letter queue for failed callbacks

4. **Dataverse Schema** (`/dataverse/schema/`)
   - `hardware-quotation-approvals.xml` - Main approval records table
   - `approval-limits.xml` - Role-based approval limit configuration

5. **Authentication** (`/authentication/`)
   - Azure AD app registration manifest
   - Teams app manifest for deployment
   - OAuth settings with role mappings

### Key Design Patterns

- **Triggered Conversations**: Bot waits for external triggers rather than user-initiated chats
- **Adaptive Cards**: Rich UI for displaying quotation details in Teams
- **Role-Based Security**: Approval limits tied to Azure AD roles
- **Audit Trail**: Every decision logged with full context
- **Resilient Callbacks**: Retry mechanism with dead letter queue for failed notifications

## Important Considerations

- All monetary values are stored in Dataverse Money type fields
- Callback URLs must use HTTPS
- Bot requires Teams channel to be enabled in Copilot Studio
- Power Automate flows need proper connections configured during deployment
- Environment variables should be used for environment-specific settings

## Testing Approach

To test the bot:
1. Deploy to a development environment first
2. Use the webhook endpoint with test payloads
3. Monitor callbacks using webhook.site or similar service
4. Check Dataverse for proper record creation
5. Verify Teams notifications are received