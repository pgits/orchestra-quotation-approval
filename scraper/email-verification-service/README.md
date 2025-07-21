# TD SYNNEX Email Verification Service

A REST API service that retrieves 2FA verification codes from Outlook emails for the TD SYNNEX scraper. This service uses Microsoft Graph API to read emails and extract verification codes automatically.

## 🚀 Quick Start

### Prerequisites

1. **Python 3.7+** installed on your system
2. **Azure AD App Registration** with proper permissions (see [Setup Guide](#azure-setup))
3. **Environment variables** configured in `.env` file

### One-Command Start

```bash
./start_email_service.sh
```

This script will automatically:
- ✅ Check prerequisites
- ✅ Create virtual environment (if needed)
- ✅ Install dependencies
- ✅ Test authentication
- ✅ Start the service
- ✅ Test all endpoints

### Manual Commands

```bash
# Start service
./start_email_service.sh start

# Stop service  
./start_email_service.sh stop

# Restart service
./start_email_service.sh restart

# Check status
./start_email_service.sh status

# Test authentication only
./start_email_service.sh test

# Show help
./start_email_service.sh help
```

## 📋 API Endpoints

Once running, the service provides these REST endpoints:

| Endpoint | Method | Description | Example |
|----------|---------|-------------|---------|
| `/status` | GET | Service status and info | `curl http://localhost:5000/status` |
| `/health` | GET | Health check with Graph API test | `curl http://localhost:5000/health` |
| `/test-email` | GET | Test connection, show recent emails | `curl http://localhost:5000/test-email` |
| `/verification-code` | GET | Get latest verification code | `curl 'http://localhost:5000/verification-code?sender=do_not_reply@tdsynnex.com'` |

### Verification Code Parameters

- `sender` (optional): Email address to filter by (default: `do_not_reply@tdsynnex.com`)
- `max_age_minutes` (optional): Maximum age of email to consider (default: `10`)
- `ignore_time_window` (optional): Set to `true` to ignore time window and search all emails (default: `false`)
- `return_verification_id` (optional): Set to `true` to return verificationId instead of verification code (default: `false`)

Examples:
```bash
# Get code from specific sender within last 5 minutes
curl 'http://localhost:5000/verification-code?sender=noreply@example.com&max_age_minutes=5'

# Get the most recent verification code ignoring time window
curl 'http://localhost:5000/verification-code?sender=do_not_reply@tdsynnex.com&ignore_time_window=true'

# Get the most recent verificationId ignoring time window  
curl 'http://localhost:5000/verification-code?sender=do_not_reply@tdsynnex.com&ignore_time_window=true&return_verification_id=true'
```

### Response Examples

**Status Response:**
```json
{
  "status": "running",
  "service": "email-verification-service", 
  "outlook_initialized": true,
  "endpoints": ["/health", "/verification-code", "/test-email", "/status"]
}
```

**Verification Code Response (Success):**
```json
{
  "success": true,
  "verification_code": "123456",
  "timestamp": "2025-07-21T14:32:00Z",
  "sender": "do_not_reply@tdsynnex.com",
  "ignore_time_window": false,
  "return_verification_id": false
}
```

**VerificationId Response (Success):**
```json
{
  "success": true,
  "verification_id": "XR0b25fc2VlX3ByaWNpbmdfX18xMA",
  "timestamp": "2025-07-21T14:49:29Z",
  "sender": "do_not_reply@tdsynnex.com",
  "ignore_time_window": true,
  "return_verification_id": true
}
```

**Response (Not Found):**
```json
{
  "success": false,
  "message": "No verification code found from do_not_reply@tdsynnex.com in the last 10 minutes",
  "timestamp": "2025-07-21T14:32:00Z"
}
```

## ⚙️ Azure Setup

### 1. Create Azure AD App Registration

Follow the detailed guide: [AZURE_APP_REGISTRATION_SETUP.md](../AZURE_APP_REGISTRATION_SETUP.md)

**Quick summary:**
1. Go to Azure Portal → Azure Active Directory → App registrations
2. Create new registration: "TD SYNNEX Email Verification Service"
3. Add API permissions: `Mail.Read` and `User.Read.All` (Application permissions)
4. **Grant admin consent** for the permissions
5. Create client secret and copy the **Value** (not Secret ID)

### 2. Environment Configuration

Create `.env` file in this directory:

```bash
# Azure AD App Registration Credentials
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here  
AZURE_CLIENT_SECRET=your-client-secret-value-here
OUTLOOK_USER_EMAIL=your-email@domain.com

# Application Settings
LOG_LEVEL=INFO
RETRY_ATTEMPTS=3
TIMEOUT_MINUTES=120
```

⚠️ **Important**: Use the client secret **Value**, not the Secret ID. The value typically starts with special characters and is longer than a GUID.

## 🔧 Integration with TD SYNNEX Scraper

The email service is designed to work with the TD SYNNEX scraper's 2FA workflow:

1. **Scraper triggers 2FA** → TD SYNNEX sends verification code email
2. **Scraper calls email service** → `GET /verification-code?sender=do_not_reply@tdsynnex.com`
3. **Service returns code** → Scraper uses code to complete authentication

### Integration Example

```python
import requests

# When 2FA is detected in scraper
def get_verification_code():
    try:
        response = requests.get(
            'http://localhost:5000/verification-code',
            params={'sender': 'do_not_reply@tdsynnex.com', 'max_age_minutes': 10}
        )
        data = response.json()
        
        if data.get('success'):
            return data['verification_code']
        else:
            print(f"No verification code found: {data.get('message')}")
            return None
            
    except Exception as e:
        print(f"Error getting verification code: {e}")
        return None

# Use in scraper
verification_code = get_verification_code()
if verification_code:
    # Enter code in 2FA form
    driver.find_element(By.ID, "verification-input").send_keys(verification_code)
```

## 📁 Project Structure

```
email-verification-service/
├── app.py                    # Main Flask application
├── outlook_client.py         # Microsoft Graph API client
├── start_email_service.sh    # Service startup script
├── requirements.txt          # Python dependencies
├── .env                     # Environment variables (create this)
├── test_auth.py             # Authentication test script
├── debug_auth.py            # Detailed auth debugging
├── Dockerfile               # Container deployment
├── README.md                # This file
└── .venv/                   # Virtual environment (auto-created)
```

## 🐛 Troubleshooting

### Common Issues

**1. Authentication Failed (401)**
- ✅ Verify client secret is the **Value**, not Secret ID
- ✅ Check if secret has expired in Azure Portal
- ✅ Ensure admin consent has been granted

**2. User Not Found (404)**
- ✅ Verify `OUTLOOK_USER_EMAIL` is correct
- ✅ Check user exists in Azure AD tenant
- ✅ Ensure user has mailbox access

**3. Permission Denied (403)**
- ✅ Verify app has `Mail.Read` and `User.Read.All` permissions
- ✅ Ensure permissions are **Application** type, not Delegated
- ✅ Check admin consent has been granted

**4. Port Already in Use**
- The script automatically finds an available port between 5000-5010
- Use `./start_email_service.sh stop` to stop existing service

### Testing Commands

```bash
# Test authentication only
./start_email_service.sh test

# Check detailed service logs
cat service.log

# Test endpoints manually
curl http://localhost:5000/health
curl http://localhost:5000/test-email

# Debug authentication issues
python3 debug_auth.py
```

### Log Files

- **service.log** - Service runtime logs
- **service.pid** - Process ID of running service

## 🔒 Security Considerations

1. **Least Privilege**: Service only has `Mail.Read` permission
2. **Secure Storage**: Store client secrets in Azure Key Vault for production
3. **Network Security**: Service runs on localhost by default
4. **Audit Logging**: All email access is logged in Azure AD audit logs
5. **Token Management**: Access tokens are automatically refreshed

## 🚀 Production Deployment

For production deployment to Azure Container Apps or similar:

1. Use environment variables instead of `.env` file
2. Store secrets in Azure Key Vault
3. Use managed identity where possible
4. Enable proper monitoring and alerting
5. Use a production WSGI server (not Flask dev server)

See `Dockerfile` for containerized deployment options.

## 📊 Monitoring

The service provides built-in health checks and logging:

- **Health Endpoint**: `/health` - Tests Graph API connectivity
- **Status Endpoint**: `/status` - Service operational status  
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Error Tracking**: Detailed error messages with correlation IDs

## 🆘 Support

If you encounter issues:

1. **Check the logs**: `cat service.log`
2. **Test authentication**: `./start_email_service.sh test`
3. **Verify Azure setup**: Review [AZURE_APP_REGISTRATION_SETUP.md](../AZURE_APP_REGISTRATION_SETUP.md)
4. **Check Azure AD audit logs** for authentication events
5. **Use Microsoft Graph Explorer** to test permissions

---

*This service is part of the TD SYNNEX scraper automation system for handling 2FA verification codes.*