# TD SYNNEX Automated Scraping System Guide

## Overview

This system provides fully automated TD SYNNEX price and availability data extraction with integrated 2FA handling. The system monitors your email for verification codes and automatically submits them to an Azure container running the scraper.

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│ Email Verification │    │ Azure Container      │    │ TD SYNNEX Portal    │
│ Service (Local)    │───▶│ Scraper (Cloud)      │───▶│ (Live Data)         │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
       │                        │                        │
       ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│ Microsoft Graph │    │ 2FA Code         │    │ Email Attachment    │
│ API Monitoring  │    │ Processing       │    │ Download            │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

## 🚀 Quick Start

### Single Command Startup
```bash
./start_td_synnex_system.sh
```

This script handles everything automatically:
- Starts the email verification service
- Connects to Azure container
- Monitors for 2FA codes
- Accounts for email delivery delays
- Submits codes and triggers scraper

## System Components

### 1. Email Verification Service (Local)
- **Location**: `./email-verification-service/`
- **Purpose**: Monitors Microsoft Outlook for TD SYNNEX 2FA codes
- **Startup**: `./email-verification-service/start_email_service.sh`
- **API Endpoint**: `http://localhost:5001`

### 2. Azure Container Scraper (Cloud)
- **Location**: Azure Container Instance
- **Purpose**: Runs TD SYNNEX scraper with received verification codes
- **Endpoint**: `http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001`
- **Deployment**: `./deploy-azure-enhanced.sh`

## ⚠️ IMPORTANT: Execution Order & Timing

### Why Order Matters
The system must account for **"snail mail delays"** - the time it takes for emails to be delivered and processed:

1. **Email Service First**: Must be monitoring BEFORE any 2FA activity
2. **Container Ready**: Azure container must be waiting for codes
3. **Timing Buffer**: Allow for email delivery delays (30+ seconds)
4. **Retry Logic**: Multiple attempts to catch delayed emails

### Recommended Startup Sequence

```bash
# Option 1: Automated (Recommended)
./start_td_synnex_system.sh

# Option 2: Manual Step-by-Step
# Step 1: Start email service first
cd email-verification-service && ./start_email_service.sh

# Step 2: Wait 10-15 seconds for service to initialize

# Step 3: Check Azure container status  
curl http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-status

# Step 4: Monitor and submit codes (with delays)
curl "http://localhost:5001/verification-code?sender=do_not_reply@tdsynnex.com&ignore_time_window=true&automatic_submit=true&target_url=http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-challenge"
```

## Email Delivery Delay Considerations

### Why Delays Happen
- Email servers may queue messages
- Microsoft Graph API sync delays
- Network latency between services
- TD SYNNEX email server processing time

### How System Handles Delays
- **60-second initial wait**: For first 2FA email to arrive after scraper starts
- **90-second intervals**: Between email checks (extended for full pipeline)
- **6 retry attempts**: Maximum monitoring cycles
- **Ignore time windows**: Processes all available codes
- **Pipeline awareness**: TD SYNNEX → Email Server → Microsoft → Graph API → Our Service

## System Flow

1. **🔄 Start Services**
   ```bash
   ./start_td_synnex_system.sh
   ```

2. **📧 Email Monitoring Active**
   - Service monitors `do_not_reply@tdsynnex.com`
   - Filters for 2FA verification emails
   - Extracts 6-digit codes from email content

3. **⏳ Code Detection & Delay Handling**
   - Checks every 30 seconds for new codes
   - Accounts for email delivery delays
   - Processes most recent verification codes

4. **🚀 Automatic Submission**
   - Posts codes to Azure container API
   - Container receives and processes codes
   - Triggers complete scraper session

5. **🎯 Scraper Execution**
   - Logs into TD SYNNEX portal
   - Applies Microsoft product filters
   - Navigates download flow: submitForm() → popup → downloadFromEc()
   - Completes request that triggers email attachment

6. **📬 Email Attachment Delivery**
   - TD SYNNEX emails price/availability data
   - Check your email for attachment file
   - File contains Microsoft product data in requested format

## Manual Operation

### Check Email Service
```bash
# Health check
curl http://localhost:5001/health

# Get latest verification code
curl "http://localhost:5001/verification-code?sender=do_not_reply@tdsynnex.com"

# Submit code manually
curl "http://localhost:5001/verification-code?automatic_submit=true&target_url=http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-challenge"
```

### Check Azure Container
```bash
# Container status
curl http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-status

# Submit code directly
curl -X POST http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-challenge \
  -H 'Content-Type: application/json' \
  -d '{"verificationId": "123456"}'
```

## Troubleshooting

### No Verification Codes Found
- **Cause**: No recent 2FA activity or email delays
- **Solution**: Wait 5-10 minutes and run script again
- **Check**: Verify TD SYNNEX login attempt triggered 2FA

### Container Not Responding  
- **Check**: Container deployment status
- **Command**: `az container show --resource-group td-synnex-scraper-2fa-rg --name td-synnex-scraper-enhanced-1753130940`
- **Fix**: Redeploy with `./deploy-azure-enhanced.sh`

### Email Service Errors
- **Check**: Microsoft Graph API authentication
- **Location**: `./email-verification-service/.env`
- **Fix**: Refresh Azure AD app credentials

### "Snail Mail" Delays
- **Symptom**: Scripts run but no codes found
- **Cause**: Email delivery taking longer than expected
- **Solution**: Re-run startup script after 5-10 minutes

## Configuration Files

### Environment Variables
- **Email Service**: `./email-verification-service/.env`
- **Scraper**: `./.env` (TD SYNNEX credentials)
- **Azure**: Environment variables in container deployment

### Key Settings
- **Initial Wait**: 60 seconds (for first 2FA email arrival)
- **Email Check Delay**: 90 seconds (extended for full email pipeline)
- **Max Retry Attempts**: 6 attempts (configurable)
- **Time Window**: Ignored (processes all available codes)
- **Container URL**: Azure container endpoint
- **Total Max Wait Time**: ~510 seconds (~8.5 minutes) for complete email delivery

## Security Notes

- All credentials stored in environment variables
- Microsoft Graph API uses OAuth2 with refresh tokens  
- Azure container uses managed identity where possible
- No sensitive data logged or transmitted in clear text

## Success Indicators

1. ✅ **Email service starts**: `Email verification service is ready`
2. ✅ **Container responds**: `Azure container is responsive`  
3. ✅ **Code found**: `Found and submitted verification code: XXXXXX`
4. ✅ **Scraper triggered**: `Scraper session initiated successfully!`
5. ✅ **Check email**: TD SYNNEX sends price/availability attachment

## Expected Output

When successful, you'll see:
```
🎉 Scraper session initiated successfully!

📬 What happens next:
   • The Azure container is now running the TD SYNNEX scraper
   • It will log in, apply Microsoft filters, and trigger download  
   • TD SYNNEX will EMAIL you the price/availability attachment
   • Check your email for the attachment file
```

The final deliverable is an **email attachment** from TD SYNNEX containing the Microsoft product price and availability data.