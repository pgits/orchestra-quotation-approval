# TD SYNNEX Local Operations Cheat Sheet

## 🏠 Local Development Workflow
**Complete flow from web scraper → email attachment → SharePoint upload**

---

## 🚀 Quick Start Commands

### 1. Start TD SYNNEX Web Scraper System
```bash
# Navigate to scraper root directory
cd /Users/petergits/dev/claude-orchestra/scraper

# Start the complete automated system (recommended)
./start_td_synnex_system.sh
```

**What this does:**
- ✅ Starts email verification service on `localhost:5001`
- ✅ Monitors for TD SYNNEX 2FA codes
- ✅ Automatically submits codes to Azure container scraper
- ✅ Triggers download process that emails attachments

### 2. Start Knowledge Update Service (Email → SharePoint)
```bash
# Navigate to knowledge update directory
cd /Users/petergits/dev/claude-orchestra/scraper/knowledge-update

# Start local knowledge update service
./start_knowledge_update_service.sh
```

**Service runs on:** `http://localhost:5000`

---

## 📋 Step-by-Step Manual Process

### Step 1: Start Email Verification Service
```bash
cd /Users/petergits/dev/claude-orchestra/scraper/email-verification-service
./start_email_service.sh
```
- **Service URL:** `http://localhost:5001`
- **Health Check:** `curl http://localhost:5001/health`

### Step 2: Start Knowledge Update Service  
```bash
cd /Users/petergits/dev/claude-orchestra/scraper/knowledge-update
./start_knowledge_update_service.sh
```
- **Service URL:** `http://localhost:5000`
- **Health Check:** `curl http://localhost:5000/health`

### Step 3: Trigger TD SYNNEX Scraper (Manual)
```bash
# Check Azure container status
curl http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-status

# Get verification code and submit (if 2FA triggered)
curl "http://localhost:5001/verification-code?sender=do_not_reply@tdsynnex.com&automatic_submit=true&target_url=http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-challenge"
```

### Step 4: Process Email Attachment to SharePoint
```bash
# Get latest TD SYNNEX attachment and upload to SharePoint
curl "http://localhost:5000/latest-attachment?ignore_time_window=true&download=true&upload_sharepoint=true"

# Or use dedicated upload endpoint
curl -X POST "http://localhost:5000/upload-to-sharepoint" \
  -H "Content-Type: application/json" \
  -d '{"overwrite": true, "cleanup_old": true}'
```

---

## 🔧 Useful Local Commands

### Email Service Operations
```bash
# Check for specific verification codes
curl "http://localhost:5001/verification-code?sender=do_not_reply@tdsynnex.com"

# Get verification code history
curl "http://localhost:5001/verification-history?sender=do_not_reply@tdsynnex.com&limit=10"

# Health check
curl "http://localhost:5001/health"
```

### Knowledge Update Service Operations  
```bash
# Get latest attachment info (no download)
curl "http://localhost:5000/latest-attachment"

# Get latest with time window override
curl "http://localhost:5000/latest-attachment?ignore_time_window=true"

# Download latest attachment content
curl "http://localhost:5000/latest-attachment?download=true"

# Upload to SharePoint with automatic cleanup
curl "http://localhost:5000/latest-attachment?ignore_time_window=true&download=true&upload_sharepoint=true"

# List existing SharePoint files
curl "http://localhost:5000/sharepoint-files"

# Get attachment history
curl "http://localhost:5000/attachment-history?days=7&limit=10"

# Service status
curl "http://localhost:5000/status"
```

### File Management
```bash
# Clean up old SharePoint files (keep latest 5)
curl -X POST "http://localhost:5000/sharepoint-cleanup" \
  -H "Content-Type: application/json" \
  -d '{"keep_latest": 5}'

# Delete specific SharePoint file
curl -X DELETE "http://localhost:5000/sharepoint-files/701601-0722-1220-1753457053.txt"
```

---

## 🔄 Complete Automated Workflow

### Option A: Fully Automated (Recommended)
```bash
# Single command that handles everything
./start_td_synnex_system.sh
```

**Process Flow:**
1. 🔷 Starts email verification service (`localhost:5001`)
2. 🔍 Monitors for TD SYNNEX 2FA emails
3. 📨 Auto-submits verification codes to Azure scraper
4. ⏳ Azure scraper logs in and triggers download
5. 📧 TD SYNNEX emails price file attachment
6. **Manual Step:** Run knowledge update service to process attachment

### Option B: Semi-Automated
```bash
# Terminal 1: Start email service
cd email-verification-service && ./start_email_service.sh

# Terminal 2: Start knowledge update service  
cd knowledge-update && ./start_knowledge_update_service.sh

# Terminal 3: Monitor and trigger
# Wait for 2FA email, then:
curl "http://localhost:5001/verification-code?sender=do_not_reply@tdsynnex.com&automatic_submit=true&target_url=http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-challenge"

# Wait for TD SYNNEX to email attachment, then:
curl "http://localhost:5000/latest-attachment?ignore_time_window=true&download=true&upload_sharepoint=true"
```

---

## 📊 Monitoring & Troubleshooting

### Service Status Checks
```bash
# Check all services are running
curl http://localhost:5001/health  # Email verification
curl http://localhost:5000/health  # Knowledge update
curl http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-status  # Azure scraper
```

### Common Issues & Solutions

**❌ Email service not finding codes:**
```bash
# Check email connectivity
curl "http://localhost:5001/health"

# Search with broader time window
curl "http://localhost:5001/verification-code?sender=do_not_reply@tdsynnex.com&max_age_minutes=120"
```

**❌ No TD SYNNEX attachments found:**
```bash
# Check recent emails
curl "http://localhost:5000/attachment-history?days=1"

# Use ignore time window
curl "http://localhost:5000/latest-attachment?ignore_time_window=true"
```

**❌ SharePoint upload failing:**
```bash
# Test SharePoint connection
curl "http://localhost:5000/sharepoint-files"

# Check service logs for permission errors
# Ensure Azure AD app has SharePoint permissions
```

---

## 🔗 Key URLs & Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| Email Verification | `http://localhost:5001` | 2FA code extraction |
| Knowledge Update | `http://localhost:5000` | Email → SharePoint processing |
| Azure Scraper | `http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001` | Web scraping container |

---

## 📁 Required Files & Configuration

### Environment Files
- `./email-verification-service/.env` - Email service credentials
- `./knowledge-update/.env` - Knowledge update service credentials

### Startup Scripts
- `./start_td_synnex_system.sh` - Master automation script
- `./email-verification-service/start_email_service.sh` - Email service
- `./knowledge-update/start_knowledge_update_service.sh` - Knowledge update service

### Key Parameters
- **Customer Number:** `701601`
- **File Pattern:** `701601-MM-DD-XXXX.txt`
- **Sender:** `do_not_reply@tdsynnex.com`
- **SharePoint Site:** `https://hexalinks.sharepoint.com/sites/QuotationsTeam`

---

## ⚡ Pro Tips

1. **Always use `ignore_time_window=true`** when testing or looking for older attachments
2. **Run services in separate terminals** for easier monitoring and debugging
3. **Check health endpoints first** before troubleshooting specific issues
4. **Use `automatic_submit=true`** for 2FA codes to trigger scraper automatically
5. **Set `upload_sharepoint=true`** in latest-attachment calls for one-step processing

---

*Last Updated: 2025-07-25*