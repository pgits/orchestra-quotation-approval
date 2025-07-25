# TD SYNNEX Azure Cloud Operations Cheat Sheet

## ☁️ Azure Cloud Workflow
**Complete cloud-based flow from web scraper → email attachment → SharePoint upload**

---

## 🚀 Quick Start - Azure Cloud Operations

### Azure Container URLs
- **Web Scraper:** `http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001`
- **Knowledge Update:** `https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io`

### One-Command Cloud Automation
```bash
# Complete cloud workflow (local email service + cloud processing)
./start_td_synnex_system.sh
```

---

## 🌐 Azure Service Endpoints

### TD SYNNEX Knowledge Update Service
**Base URL:** `https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io`

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/health` | GET | Service health check | Health probe |
| `/latest-attachment` | GET | Get latest TD SYNNEX file | Main processing endpoint |
| `/upload-to-sharepoint` | POST | Upload file to SharePoint | Dedicated upload |
| `/sharepoint-files` | GET | List existing files | File management |
| `/attachment-history` | GET | Email attachment history | Audit trail |
| `/sharepoint-cleanup` | POST | Clean up old files | Maintenance |

### TD SYNNEX Web Scraper Service  
**Base URL:** `http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001`

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/2fa-status` | GET | Check scraper status | Status check |
| `/2fa-challenge` | POST | Submit verification code | 2FA submission |
| `/health` | GET | Container health | Health probe |

---

## 🔄 Azure Cloud Workflow Commands

### Step 1: Check Azure Services Status
```bash
# Check knowledge update service
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/health"

# Check web scraper service
curl "http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-status"
```

### Step 2: Process Latest TD SYNNEX Attachment (Cloud)
```bash
# Get latest attachment and upload to SharePoint (cloud processing)
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/latest-attachment?ignore_time_window=true&download=true&upload_sharepoint=true"
```

### Step 3: Manual File Upload to SharePoint (Cloud)
```bash
# Upload specific file with cleanup
curl -X POST "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/upload-to-sharepoint" \
  -H "Content-Type: application/json" \
  -d '{
    "overwrite": true,
    "cleanup_old": true,
    "max_age_minutes": 60
  }'
```

---

## 🎯 Azure-Specific Operations

### File Management in Cloud
```bash
# List SharePoint files (cloud service)
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/sharepoint-files"

# Get attachment history (cloud service)
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/attachment-history?days=7&limit=10"

# Clean up old files (keep latest 5)
curl -X POST "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/sharepoint-cleanup" \
  -H "Content-Type: application/json" \
  -d '{"keep_latest": 5}'
```

### Monitoring & Status
```bash
# Service status
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/status"

# Health check with detailed info
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/health"
```

---

## 🔧 Azure Deployment & Management

### Deploy Knowledge Update Service
```bash
cd /Users/petergits/dev/claude-orchestra/scraper/knowledge-update

# Full deployment pipeline
./deploy-azure.sh all

# Individual steps
./deploy-azure.sh build    # Build Docker image
./deploy-azure.sh push     # Push to Azure Container Registry  
./deploy-azure.sh deploy   # Deploy to Azure Container Apps
```

### Azure Container Management
```bash
# Check container app status
az containerapp show \
  --name "td-synnex-knowledge-update" \
  --resource-group "td-synnex-scraper-rg"

# View container logs
az containerapp logs show \
  --name "td-synnex-knowledge-update" \
  --resource-group "td-synnex-scraper-rg" \
  --follow

# Scale container app
az containerapp update \
  --name "td-synnex-knowledge-update" \
  --resource-group "td-synnex-scraper-rg" \
  --min-replicas 1 \
  --max-replicas 5
```

---

## ⚡ Azure Automation Workflows

### Hybrid Approach (Local Email + Cloud Processing)
```bash
# Terminal 1: Start local email verification service
cd /Users/petergits/dev/claude-orchestra/scraper/email-verification-service
./start_email_service.sh

# Terminal 2: Use cloud services for processing
# Wait for 2FA email, then submit to cloud scraper
curl "http://localhost:5001/verification-code?sender=do_not_reply@tdsynnex.com&automatic_submit=true&target_url=http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-challenge"

# Wait for TD SYNNEX email attachment, then process with cloud service
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/latest-attachment?ignore_time_window=true&download=true&upload_sharepoint=true"
```

### Full Cloud Automation (Future - requires cloud email service)
```bash
# Once email service is also containerized:
# This would be the complete cloud workflow

# 1. Trigger cloud scraper directly
curl -X POST "http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/start-scraper" \
  -H "Content-Type: application/json" \
  -d '{"auto_2fa": true}'

# 2. Process resulting attachment via cloud service
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/latest-attachment?ignore_time_window=true&download=true&upload_sharepoint=true"
```

---

## 📊 Azure Configuration Details

### Container App Configuration
```yaml
Resource Details:
  Name: td-synnex-knowledge-update
  Resource Group: td-synnex-scraper-rg
  Environment: td-synnex-env
  Registry: tdsynnexscraperacr.azurecr.io
  
Compute:
  CPU: 1.0 cores
  Memory: 2Gi
  Replicas: 1-3 (auto-scaling)
  
Network:
  External Ingress: HTTPS
  Port: 5000
  FQDN: td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io
```

### Environment Variables (Cloud)
```bash
# These are configured in Azure Container Apps environment
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<client-id>
AZURE_CLIENT_SECRET=<client-secret>
OUTLOOK_USER_EMAIL=<email>
CUSTOMER_NUMBER=701601
SHAREPOINT_SITE_URL=https://hexalinks.sharepoint.com/sites/QuotationsTeam
SHAREPOINT_FOLDER_PATH=Shared Documents/Quotations-Team-Channel
```

---

## 🚨 Azure Troubleshooting

### Common Issues & Cloud Solutions

**❌ Container not responding:**
```bash
# Check container status
az containerapp show --name "td-synnex-knowledge-update" --resource-group "td-synnex-scraper-rg"

# Restart container
az containerapp revision restart \
  --name "td-synnex-knowledge-update" \
  --resource-group "td-synnex-scraper-rg"
```

**❌ Authentication issues:**
```bash
# Check Azure AD app permissions
az ad app permission list --id <client-id>

# Test authentication manually
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/health"
```

**❌ SharePoint access denied:**
```bash
# List SharePoint files to test permissions
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/sharepoint-files"

# Check detailed error in logs
az containerapp logs show \
  --name "td-synnex-knowledge-update" \
  --resource-group "td-synnex-scraper-rg" \
  --tail 100
```

---

## 🔄 Production Automation Examples

### Scheduled Processing (Azure Logic Apps Integration)
```bash
# Example webhook call for scheduled processing
curl -X POST "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/webhook/power-automate" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "scheduled_check",
    "trigger": "logic_app",
    "process_latest": true
  }'
```

### Batch Processing
```bash
# Process multiple recent attachments
for i in {1..5}; do
  echo "Processing attempt $i..."
  curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/latest-attachment?ignore_time_window=true&download=true&upload_sharepoint=true"
  sleep 30
done
```

### Monitoring Script
```bash
#!/bin/bash
# Azure service monitoring script

echo "🔍 Checking Azure TD SYNNEX Services..."

# Check knowledge update service
if curl -f "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/health" > /dev/null 2>&1; then
  echo "✅ Knowledge Update Service: OK"
else
  echo "❌ Knowledge Update Service: FAILED"
fi

# Check web scraper service  
if curl -f "http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-status" > /dev/null 2>&1; then
  echo "✅ Web Scraper Service: OK"
else
  echo "❌ Web Scraper Service: FAILED"
fi

# Check SharePoint connectivity
SHAREPOINT_CHECK=$(curl -s "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/sharepoint-files")
if echo "$SHAREPOINT_CHECK" | grep -q "success.*true"; then
  echo "✅ SharePoint Integration: OK"
else
  echo "❌ SharePoint Integration: FAILED"
fi
```

---

## 📈 Performance & Scaling

### Auto-scaling Configuration
```bash
# Update scaling rules
az containerapp update \
  --name "td-synnex-knowledge-update" \
  --resource-group "td-synnex-scraper-rg" \
  --min-replicas 1 \
  --max-replicas 5 \
  --scale-rule-name "http-scale" \
  --scale-rule-type "http" \
  --scale-rule-http-concurrency 10
```

### Performance Testing
```bash
# Load test the service
for i in {1..10}; do
  curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/health" &
done
wait

# Test file processing performance
time curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/latest-attachment?ignore_time_window=true&download=true"
```

---

## 🔐 Security & Compliance

### Azure AD Permissions Required
- **Microsoft Graph API**: `Mail.Read`, `Sites.ReadWrite.All`
- **SharePoint**: Site collection access to QuotationsTeam site
- **Authentication**: Client credentials flow with Azure AD app

### HTTPS & SSL
- All cloud endpoints use HTTPS by default
- Azure Container Apps provides SSL termination
- Internal communication uses secure protocols

---

*Azure Services Last Updated: 2025-07-25*
*Cloud URLs valid as of deployment date*