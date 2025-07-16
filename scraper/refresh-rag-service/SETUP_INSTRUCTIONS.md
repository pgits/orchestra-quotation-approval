# No-CLI Setup Instructions

## Overview
This setup avoids all CLI installation issues by using web interfaces and direct HTTP calls.

## Step 1: Deploy Power Automate Flow

1. **Go to Power Automate**
   - Visit: https://powerautomate.microsoft.com
   - Sign in with your Microsoft 365 account

2. **Import the Flow**
   - Click "My flows" → "Import" → "Import Package (Legacy)"
   - Upload: `flows/copilot-knowledge-refresh-flow.json`

3. **Configure Connections**
   - **Dataverse**: Connect to your environment
   - **OneDrive for Business**: Connect to your OneDrive

4. **Set Parameters**
   - Find the "CopilotStudioAgentId" parameter
   - We'll set this in the next step

## Step 2: Find Your Agent ID

1. **Go to Copilot Studio**
   - Visit: https://copilotstudio.microsoft.com
   - Navigate to your environment

2. **Find Your Agent**
   - Look for "Nathan's Hardware Buddy v.1"
   - Click on the agent
   - Copy the Agent ID from the URL or agent properties

## Step 3: Get Flow Trigger URL

1. **Open Your Flow**
   - Go back to Power Automate
   - Open your imported flow

2. **Get Trigger URL**
   - Click on the "Request" trigger (first step)
   - Copy the "HTTP POST URL"

## Step 4: Configure the System

Run the configuration wizard:
```bash
python3 scripts/config-wizard.py
```

Enter:
- Your Agent ID (from Step 2)
- Your Environment ID (optional)
- Your Flow Trigger URL (from Step 3)

## Step 5: Test Upload

```bash
python3 scripts/upload-to-copilot.py ~/Downloads/ec-synnex-701601-0708-0927.xls
```

## Troubleshooting

- **File not found**: Check the file path
- **Trigger URL error**: Verify the URL from Power Automate
- **Agent ID error**: Make sure you copied the correct ID from Copilot Studio
- **Connection errors**: Check your internet connection and Microsoft 365 access

## Automation

To automate uploads, add to crontab:
```bash
crontab -e
# Add: 0 9 * * * cd /path/to/refresh-rag-service && python3 scripts/upload-to-copilot.py ~/Downloads/ec-synnex-701601-0708-0927.xls
```
