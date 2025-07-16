# Test Proxy for 2FA Authentication Capture

This mitmproxy-based test proxy captures HTTP/HTTPS traffic for analyzing 2-factor authentication flows.

## Quick Start

### 1. Deploy to Azure
```bash
cd /Users/petergits/dev/claude-orchestra/scraper/test-proxy
./deploy-azure.sh
```

### 2. Configure Your Browser
After deployment, you'll get a URL like: `http://test-proxy-2fa.eastus.azurecontainer.io`

**Configure Browser Proxy:**
1. Go to browser settings → Network/Proxy settings
2. Set HTTP/HTTPS proxy to: `test-proxy-2fa.eastus.azurecontainer.io:8080`
3. Make sure to include port 8080

**Install Certificate for HTTPS:**
1. With proxy configured, visit: `http://mitm.it`
2. Download and install the certificate for your browser
3. Restart browser after installation

### 3. Monitor Traffic
- **Web Interface**: `http://test-proxy-2fa.eastus.azurecontainer.io:8081`
- **Real-time monitoring**: Shows all requests/responses as they happen
- **Authentication flows**: Automatically highlighted and logged

## Features

### Automatic 2FA Detection
- Captures all authentication-related domains:
  - `login.microsoftonline.com`
  - `account.live.com`
  - `login.live.com`
  - `accounts.google.com`
  - `hexalinks.sharepoint.com`
  - `tdsynnex.com`

### Detailed Logging
- All authentication requests/responses
- Form data and JSON payloads
- Cookie setting and redirects
- Error responses with content

### Export Capabilities
- JSON export of captured flows
- Detailed request/response data
- Timestamps and flow relationships

## Usage

1. **Start proxy** (automatically happens on Azure deployment)
2. **Configure browser** to use proxy
3. **Install certificate** for HTTPS interception
4. **Navigate to authentication flow** in browser
5. **Monitor web interface** for real-time capture
6. **Export data** from web interface when done

## Files Generated

- `/app/logs/mitm.log` - Detailed proxy logs
- `/app/logs/captured_flows.json` - Structured flow data
- Web interface provides additional export options

## Troubleshooting

### Certificate Issues
- Make sure to visit `http://mitm.it` (not https)
- Clear browser cache after installing certificate
- Restart browser after certificate installation

### Proxy Not Working
- Check browser proxy settings include port 8080
- Verify container is running: `az container logs --resource-group test-proxy-rg --name test-proxy-2fa --follow`
- Test with simple HTTP site first before HTTPS

### No Traffic Captured
- Verify proxy is configured correctly in browser
- Check if certificate is installed for HTTPS sites
- Look at container logs for any errors

## Azure Management

### View Logs
```bash
az container logs --resource-group test-proxy-rg --name test-proxy-2fa --follow
```

### Restart Container
```bash
az container restart --resource-group test-proxy-rg --name test-proxy-2fa
```

### Delete Resources
```bash
az group delete --name test-proxy-rg --yes --no-wait
```

## Security Notes

- This proxy captures all HTTP/HTTPS traffic - only use for testing
- Deploy in secure Azure environment
- Delete resources when testing is complete
- Don't use for production traffic or sensitive data beyond testing scope