# Chrome Installation Guide for Azure Functions

This guide provides multiple approaches to install Chrome in Azure Functions for web scraping.

## 🚨 Important Notes

Azure Functions **Consumption Plan** has significant limitations:
- No persistent storage between executions
- Limited write access to system directories
- No package manager access (apt, yum, etc.)
- 10-minute execution timeout

**Recommended**: Use **Premium Plan** or **Dedicated Plan** for better Chrome support.

## Approach 1: Containerized Deployment (Recommended)

### Prerequisites
- Docker installed locally
- Azure Container Registry created
- Azure Functions Premium Plan

### Steps

1. **Build and deploy using Docker**:
   ```bash
   # Run the Docker deployment script
   ./docker-deploy.sh
   ```

2. **Or manually**:
   ```bash
   # Build image
   docker build -f Dockerfile.azure -t tdsynnex-scraper-func .
   
   # Tag for ACR
   docker tag tdsynnex-scraper-func tdsynnexscraperacr.azurecr.io/tdsynnex-scraper-func:latest
   
   # Login and push
   az acr login --name tdsynnexscraperacr
   docker push tdsynnexscraperacr.azurecr.io/tdsynnex-scraper-func:latest
   
   # Configure Function App
   az functionapp config container set \
     --name tdsynnex-scraper-func \
     --resource-group td-synnex-scraper-rg \
     --docker-custom-image-name tdsynnexscraperacr.azurecr.io/tdsynnex-scraper-func:latest
   ```

## Approach 2: Runtime Chrome Installation

### Method A: Python Chrome Installer (Automatic)

The function includes `chrome_installer.py` that automatically:
1. Downloads Chrome binary from Google's testing repository
2. Downloads ChromeDriver
3. Installs to `/tmp/chrome_install/`
4. Sets environment variables

**Usage**: Already integrated in the function code.

### Method B: Manual Chrome Installation

1. **Access Function App via SSH** (Premium Plan only):
   ```bash
   az webapp ssh --name tdsynnex-scraper-func --resource-group td-synnex-scraper-rg
   ```

2. **Install Chrome manually**:
   ```bash
   # Update package list
   apt-get update
   
   # Install dependencies
   apt-get install -y wget gnupg software-properties-common
   
   # Add Google Chrome repository
   wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
   echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
   
   # Update and install Chrome
   apt-get update
   apt-get install -y google-chrome-stable
   
   # Install ChromeDriver
   CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
   wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
   unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
   chmod +x /usr/local/bin/chromedriver
   ```

3. **Set Application Settings**:
   ```bash
   az functionapp config appsettings set \
     --name tdsynnex-scraper-func \
     --resource-group td-synnex-scraper-rg \
     --settings \
       CHROME_BIN=/usr/bin/google-chrome-stable \
       CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
   ```

## Approach 3: Azure Functions Extensions

### Method A: Using SCM Site (Kudu)

1. **Access Kudu console**:
   ```
   https://tdsynnex-scraper-func.scm.azurewebsites.net/
   ```

2. **Navigate to Debug Console > CMD**

3. **Run installation commands**:
   ```bash
   cd D:\home\site\wwwroot
   
   # Download Chrome installer script
   curl -o install_chrome.sh https://raw.githubusercontent.com/your-repo/install_chrome.sh
   
   # Make executable and run
   chmod +x install_chrome.sh
   ./install_chrome.sh
   ```

### Method B: Using Azure Functions Core Tools

1. **Connect to Function App**:
   ```bash
   func azure functionapp logstream tdsynnex-scraper-func
   ```

2. **Use startup script**: Place `startup.sh` in the function root and configure it to run on startup.

## Approach 4: Azure Container Instances Alternative

If Azure Functions proves too restrictive, consider using Azure Container Instances:

1. **Create Container Instance**:
   ```bash
   az container create \
     --resource-group td-synnex-scraper-rg \
     --name td-synnex-scraper-container \
     --image tdsynnexscraperacr.azurecr.io/tdsynnex-scraper-func:latest \
     --registry-login-server tdsynnexscraperacr.azurecr.io \
     --registry-username $(az acr credential show --name tdsynnexscraperacr --query username -o tsv) \
     --registry-password $(az acr credential show --name tdsynnexscraperacr --query passwords[0].value -o tsv) \
     --cpu 2 \
     --memory 4 \
     --restart-policy OnFailure
   ```

2. **Call via HTTP trigger** or **scheduled execution**.

## Troubleshooting

### Common Issues

1. **Chrome binary not found**:
   ```bash
   # Check if Chrome is installed
   ls -la /usr/bin/google-chrome*
   ls -la /tmp/chrome_install/
   
   # Check environment variables
   echo $CHROME_BIN
   echo $CHROMEDRIVER_PATH
   ```

2. **Permission denied**:
   ```bash
   # Fix permissions
   chmod +x /usr/bin/google-chrome-stable
   chmod +x /usr/local/bin/chromedriver
   ```

3. **Missing dependencies**:
   ```bash
   # Install missing libraries
   apt-get install -y libgconf-2-4 libxss1 libxtst6 libxrandr2 libasound2 libpangocairo-1.0-0 libatk1.0-0 libcairo1 libgtk-3-0 libgdk-pixbuf2.0-0
   ```

### Testing Chrome Installation

1. **Test Chrome version**:
   ```bash
   /usr/bin/google-chrome-stable --version
   ```

2. **Test ChromeDriver**:
   ```bash
   /usr/local/bin/chromedriver --version
   ```

3. **Test function**:
   ```bash
   curl -X POST "https://tdsynnex-scraper-func.azurewebsites.net/api/scrape?code=YOUR_CODE" \
     -H "Content-Type: application/json" \
     -d '{"test": false}'
   ```

## Performance Considerations

1. **Use Premium Plan** for better performance and no cold starts
2. **Enable Application Insights** for monitoring
3. **Set appropriate timeout** in host.json (max 10 minutes for Consumption)
4. **Consider scaling** based on load

## Security Notes

1. **Never commit credentials** to the repository
2. **Use Key Vault** for sensitive configuration
3. **Enable managed identity** for Azure resource access
4. **Regular security updates** for Chrome and dependencies

## Alternative Solutions

If Chrome installation proves too complex:

1. **Use headless browser services** (e.g., Puppeteer as a service)
2. **Azure Logic Apps** with HTTP connectors
3. **Azure Automation** runbooks
4. **Third-party scraping APIs**

---

**Next Steps**: Try the containerized approach first, then fall back to runtime installation if needed.