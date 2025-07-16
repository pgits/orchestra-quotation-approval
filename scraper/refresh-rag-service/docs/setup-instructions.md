# Copilot Studio Knowledge Base Refresh Service

## Overview

This service automates the process of updating knowledge base files in your Copilot Studio agent "Nathan's Hardware Buddy v.1". It replaces existing `ec-synnex-*-*.xls` files with new versions automatically using Power Automate flows.

## Prerequisites

- macOS (tested on macOS 14+)
- Administrator access to your Mac
- Microsoft 365 account with access to:
  - Power Automate
  - Copilot Studio
  - Dataverse
  - OneDrive for Business

## Quick Start

### 1. Initial Setup

Run the setup script to install all prerequisites:

```bash
cd refresh-rag-service
./scripts/setup-macos.sh
```

This will install:
- Homebrew (if not present)
- Python 3 and required packages
- Power Platform CLI
- jq (JSON processor)
- Create necessary directories

### 2. Get Your Agent ID

```bash
./scripts/get-agent-id.sh -AgentName "Nathan's Hardware Buddy v.1"
```

This will:
- Find your Copilot Studio agent
- Display the Agent ID
- Automatically update `config/config.json` with the correct ID

### 3. Configure the Service

Edit `config/config.json` and update the following values:

```json
{
  "copilotStudio": {
    "agentId": "YOUR_AGENT_ID_FROM_STEP_2",
    "environment": {
      "id": "YOUR_ENVIRONMENT_ID"
    }
  },
  "powerAutomate": {
    "triggerUrl": "YOUR_FLOW_TRIGGER_URL_AFTER_DEPLOYMENT"
  }
}
```

### 4. Deploy the Power Automate Flow

```bash
./scripts/deploy-flow.sh -EnvironmentId "YOUR_ENVIRONMENT_ID" -SubscriptionId "YOUR_SUBSCRIPTION_ID" -ResourceGroupName "YOUR_RESOURCE_GROUP"
```

Follow the manual deployment steps provided by the script.

### 5. Test the Upload

```bash
./scripts/upload-file.sh ~/Downloads/ec-synnex-701601-0708-0927.xls
```

## Detailed Setup Instructions

### Power Automate Flow Deployment

1. **Open Power Automate Portal**
   - Go to https://powerautomate.microsoft.com
   - Navigate to your target environment

2. **Import the Flow**
   - Click "My flows" → "Import" → "Import Package (Legacy)"
   - Upload `flows/copilot-knowledge-refresh-flow-updated.json`

3. **Configure Connections**
   - **Dataverse Connection**: Connect to your Dataverse environment
   - **OneDrive Connection**: Connect to your OneDrive for Business account

4. **Set Parameters**
   - Set `CopilotStudioAgentId` to your agent's ID
   - Save the flow

5. **Get Trigger URL**
   - Open the flow
   - Click on the "Request" trigger
   - Copy the "HTTP POST URL"
   - Update `config/config.json` with this URL

### Authentication Setup

1. **Power Platform CLI Authentication**
   ```bash
   pac auth create --tenant YOUR_TENANT_ID
   pac org select --environment YOUR_ENVIRONMENT_ID
   ```

2. **Test Authentication**
   ```bash
   pac copilot list
   ```

## Usage

### Manual Upload

Upload a specific file:
```bash
./scripts/upload-file.sh /path/to/your/file.xls
```

Upload using default configuration:
```bash
./scripts/upload-file.sh
```

### Automated Upload (Cron Job)

Set up automatic uploads every day at 9 AM:

```bash
crontab -e
```

Add this line:
```cron
0 9 * * * /Users/petergits/dev/claude-orchestra/scraper/refresh-rag-service/scripts/upload-file.sh
```

## File Structure

```
refresh-rag-service/
├── config/
│   └── config.json                    # Configuration file
├── docs/
│   └── setup-instructions.md          # This file
├── flows/
│   ├── copilot-knowledge-refresh-flow.json       # Original flow definition
│   └── copilot-knowledge-refresh-flow-updated.json # Updated with connections
├── scripts/
│   ├── setup-macos.sh                 # macOS setup script
│   ├── get-agent-id.sh                # Get Copilot Studio agent ID
│   ├── deploy-flow.sh                 # Deploy Power Automate flow
│   ├── upload-file.sh                 # Main upload script
│   └── upload-file.py                 # Python upload script
└── logs/
    ├── upload.log                     # Upload logs
    └── audit.jsonl                    # Audit trail
```

## How It Works

1. **File Validation**: The script validates the file exists, has correct extension, and is within size limits
2. **Existing File Cleanup**: Power Automate flow finds and deletes existing `ec-synnex-*` files
3. **File Upload**: New file is uploaded to OneDrive and then to Dataverse
4. **Knowledge Base Update**: Copilot Studio processes the new file and updates the knowledge base
5. **Audit Trail**: All actions are logged for compliance and debugging

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   pac auth create --tenant YOUR_TENANT_ID
   ```

2. **File Too Large**
   - Check file size limits in config.json
   - Maximum supported: 512MB

3. **Flow Not Triggering**
   - Verify trigger URL in config.json
   - Check Power Automate flow is enabled
   - Verify connections are working

4. **Agent Not Found**
   - Verify agent name is exact match
   - Check environment ID is correct
   - Ensure you have access to the agent

### Logs

- Upload logs: `logs/upload.log`
- Audit trail: `logs/audit.jsonl`
- Verbose logging: Use `./scripts/upload-file.sh -v`

### Support

For issues with:
- **Power Platform CLI**: https://docs.microsoft.com/en-us/power-platform/developer/cli/
- **Power Automate**: https://docs.microsoft.com/en-us/power-automate/
- **Copilot Studio**: https://docs.microsoft.com/en-us/microsoft-copilot-studio/

## Security Considerations

- Configuration file contains sensitive information - keep it secure
- Audit trail is enabled by default for compliance
- All API calls use HTTPS
- File validation prevents malicious uploads

## Maintenance

### Regular Tasks

1. **Monitor logs** for errors or issues
2. **Update file patterns** if naming conventions change
3. **Review audit trail** for compliance
4. **Clean up old logs** based on retention policy

### Updates

To update the service:
1. Pull latest changes
2. Run setup script again if needed
3. Redeploy flow if schema changes
4. Update configuration as needed