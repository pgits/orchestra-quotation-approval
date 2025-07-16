# Browser Configuration Guide for Test Proxy

## Your Test Proxy Details

**Proxy Server**: `test-proxy-2fa.eastus.azurecontainer.io:8080`
**Web Interface**: `http://20.246.169.16:8081` (must use IP address for security)

## Step 1: Configure Browser Proxy Settings

### Chrome/Chromium:
1. Open Chrome Settings
2. Search for "proxy" or go to Advanced → System
3. Click "Open your computer's proxy settings"
4. Enable "Use a proxy server"
5. Set Address: `test-proxy-2fa.eastus.azurecontainer.io`
6. Set Port: `8080`
7. Check "Use this proxy server for all protocols"
8. Click "Save"

### Firefox:
1. Open Firefox Settings
2. Search for "proxy" or go to General → Network Settings
3. Click "Settings..." button
4. Select "Manual proxy configuration"
5. HTTP Proxy: `test-proxy-2fa.eastus.azurecontainer.io`
6. Port: `8080`
7. Check "Use this proxy server for all protocols"
8. Click "OK"

### Safari:
1. Open Safari Preferences
2. Go to Advanced tab
3. Click "Change Settings..." next to Proxies
4. Check "Web Proxy (HTTP)" and "Secure Web Proxy (HTTPS)"
5. Enter: `test-proxy-2fa.eastus.azurecontainer.io:8080`
6. Click "OK" and "Apply"

## Step 2: Install mitmproxy Certificate for HTTPS

**Important**: Without the certificate, you can only capture HTTP traffic, not HTTPS.

### Install Certificate:
1. **With proxy configured**, navigate to: `http://mitm.it`
2. Download the certificate for your operating system:
   - **Windows**: Download `.p12` file
   - **macOS**: Download `.pem` file  
   - **Linux**: Download `.pem` file

### Install Certificate by OS:

#### Windows:
1. Double-click the downloaded `.p12` file
2. Follow the Certificate Import Wizard
3. Choose "Current User" store
4. Enter password (if prompted)
5. Place certificate in "Trusted Root Certification Authorities"
6. Restart browser

#### macOS:
1. Double-click the downloaded `.pem` file
2. Keychain Access will open
3. Find "mitmproxy" certificate
4. Double-click and set "Trust" to "Always Trust"
5. Restart browser

#### Linux:
1. Copy certificate to trusted store:
   ```bash
   sudo cp mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy.crt
   sudo update-ca-certificates
   ```
2. For Firefox specifically, import in browser settings
3. Restart browser

## Step 3: Test the Setup

1. **Test HTTP**: Visit `http://httpbin.org/get` 
   - Should work normally and appear in proxy logs

2. **Test HTTPS**: Visit `https://httpbin.org/get`
   - Should work normally if certificate is installed correctly
   - If you get certificate errors, certificate installation failed

3. **Check Web Interface**: Open `http://20.246.169.16:8081`
   - Should show mitmproxy web interface
   - Should display captured traffic in real-time

## Step 4: Verify 2FA Capture

1. Navigate to a site that requires 2FA (like Microsoft 365)
2. Go through the login process
3. In the web interface, you should see:
   - All authentication requests
   - Form data submissions
   - Redirects and callbacks
   - Cookie setting
   - 2FA challenge responses

## Troubleshooting

### Common Issues:

#### "This site can't be reached" errors:
- Check proxy settings are correct
- Verify container is running: `az container show --resource-group test-proxy-rg --name test-proxy-2fa`

#### Certificate warnings for HTTPS sites:
- Certificate not installed correctly
- Try visiting `http://mitm.it` again with proxy enabled
- Clear browser cache and restart

#### Web interface not loading:
- Check URL: `http://20.246.169.16:8081`
- Verify container ports are open
- Check container logs for errors

#### No traffic appearing in web interface:
- Verify proxy is configured correctly
- Check browser isn't bypassing proxy
- Look for browser proxy bypass settings

### Advanced Troubleshooting:

#### Check container status:
```bash
az container logs --resource-group test-proxy-rg --name test-proxy-2fa
```

#### Test proxy directly:
```bash
curl -x test-proxy-2fa.eastus.azurecontainer.io:8080 http://httpbin.org/get
```

#### Restart container if needed:
```bash
az container restart --resource-group test-proxy-rg --name test-proxy-2fa
```

## When You're Done

**Remember to disable proxy settings** when finished testing:
1. Go back to proxy settings in your browser
2. Disable proxy or set to "No proxy"
3. Restart browser

## Cleanup Azure Resources

When completely done with testing:
```bash
az group delete --name test-proxy-rg --yes --no-wait
```

This will remove all proxy resources and stop charges.