# TD SYNNEX Microsoft Product Scraper

An automated web scraper that monitors TD SYNNEX for Microsoft product inventory and integrates with Microsoft Copilot Studio for the "Nathan's Hardware Buddy v.1" agent.

## Overview

This system automates the following workflow:
1. Logs into TD SYNNEX portal twice daily (10:00 AM & 5:55 PM EST)
2. Filters and downloads Microsoft product inventory data
3. Monitors email for download confirmations
4. Forwards data to pgits@hexalinks.com for Copilot processing
5. Updates SharePoint knowledge base for the Copilot agent

## Features

- **Automated Scheduling**: Runs twice daily at configured times
- **Intelligent Filtering**: Uses HuggingFace models to identify Microsoft products
- **Email Monitoring**: Waits for and processes TD SYNNEX email confirmations
- **Failure Notifications**: Sends alerts to pgits@hexalinks.com on failures
- **Docker Support**: Containerized deployment with Docker Compose
- **Cloud Ready**: Includes Kubernetes and Azure deployment configurations

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- TD SYNNEX account credentials
- Email account with IMAP/SMTP access
- Microsoft Power Platform access (for Copilot integration)

### Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd td-synnex-scraper
```

2. Create environment configuration:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the scraper:
```bash
python -m src.scraper.main
```

### Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up -d
```

2. View logs:
```bash
docker-compose logs -f td-synnex-scraper
```

3. Stop the service:
```bash
docker-compose down
```

## Configuration

### Environment Variables

Key configuration variables in `.env`:

- `TDSYNNEX_USERNAME`: Your TD SYNNEX username
- `TDSYNNEX_PASSWORD`: Your TD SYNNEX password
- `EMAIL_USERNAME`: Email account for monitoring
- `EMAIL_PASSWORD`: Email account password
- `IMAP_SERVER`: IMAP server address (default: imap.gmail.com)
- `SMTP_SERVER`: SMTP server address (default: smtp.gmail.com)

### Microsoft Azure Setup

#### Step 1: Create Azure Resources

1. **Access Azure Portal**:
   - Navigate to [portal.azure.com](https://portal.azure.com)
   - Sign in with your Microsoft account

2. **Create Resource Group**:
   - Click "Resource groups" in the left menu
   - Click "+ Create"
   - Enter Resource Group Name: `rg-td-synnex-scraper`
   - Select your subscription
   - Choose Region: `East US` or your preferred region
   - Click "Review + create" → "Create"

3. **Create Container Registry** (if using custom images):
   - Search "Container Registry" in the top search bar
   - Click "+ Create"
   - Select your subscription and resource group
   - Registry name: `tdsynnexscraper` (must be globally unique)
   - Location: Same as resource group
   - SKU: `Basic`
   - Click "Review + create" → "Create"

4. **Create Storage Account** (for logs and data):
   - Search "Storage accounts" in the top search bar
   - Click "+ Create"
   - Select your subscription and resource group
   - Storage account name: `tdsynnexlogs` (must be globally unique)
   - Region: Same as resource group
   - Performance: `Standard`
   - Redundancy: `Locally redundant storage (LRS)`
   - Click "Review + create" → "Create"

#### Step 2: Deploy Container Instance

1. **Using Azure CLI** (Recommended):
   ```bash
   # Login to Azure
   az login
   
   # Set subscription (if you have multiple)
   az account set --subscription "Your Subscription Name"
   
   # Deploy using ARM template
   az deployment group create \
     --resource-group rg-td-synnex-scraper \
     --template-file deployment/azure/arm_template.json \
     --parameters \
       containerName=td-synnex-scraper \
       imageUri=mcr.microsoft.com/azuredocs/aci-helloworld \
       tdSynnexUsername="your_username" \
       tdSynnexPassword="your_password" \
       emailUsername="your_email@domain.com" \
       emailPassword="your_email_password"
   ```

2. **Using Azure Portal**:
   - Search "Container Instances" in the top search bar
   - Click "+ Create"
   - Select your subscription and resource group
   - Container name: `td-synnex-scraper`
   - Region: Same as resource group
   - Image source: `Other registry`
   - Image type: `Public`
   - Image: `your-registry/td-synnex-scraper:latest`
   - OS type: `Linux`
   - Size: 2 vCPU, 4 GB memory
   - Click "Next: Networking"
   - Networking type: `Public`
   - DNS name label: `td-synnex-scraper-unique`
   - Ports: `8080` (TCP)
   - Click "Next: Advanced"
   - Environment variables:
     - `TDSYNNEX_USERNAME` = `your_username` (Secure)
     - `TDSYNNEX_PASSWORD` = `your_password` (Secure)
     - `EMAIL_USERNAME` = `your_email@domain.com` (Secure)
     - `EMAIL_PASSWORD` = `your_email_password` (Secure)
     - `LOG_LEVEL` = `INFO`
   - Click "Review + create" → "Create"

#### Step 3: Monitor Deployment

1. **Check Container Status**:
   - Go to your Container Instance in Azure Portal
   - Check "Overview" tab for status
   - Monitor "Logs" tab for application logs
   - Use "Connect" tab for troubleshooting

2. **Set up Monitoring**:
   - Navigate to "Monitoring" → "Logs"
   - Create custom queries for scraper events
   - Set up alerts for failures

### Microsoft Power Platform Setup

#### Step 1: Access Power Platform

1. **Navigate to Power Platform Admin Center**:
   - Go to [admin.powerplatform.microsoft.com](https://admin.powerplatform.microsoft.com)
   - Sign in with your Microsoft 365 admin account

2. **Create or Select Environment**:
   - Click "Environments" in the left menu
   - Either select existing environment or click "+ New"
   - For new environment:
     - Name: `Nathan Hardware Buddy Production`
     - Type: `Production`
     - Region: Choose your region
     - Create Dataverse database: `Yes`
     - Language: `English`
     - Currency: `US Dollar`
     - Click "Save"

#### Step 2: SharePoint Site Setup

1. **Create SharePoint Site**:
   - Navigate to [admin.microsoft.com](https://admin.microsoft.com)
   - Go to "Admin centers" → "SharePoint"
   - Click "Sites" → "Active sites"
   - Click "+ Create"
   - Choose "Team site"
   - Site name: `Nathan's Hardware Buddy`
   - Site address: `nathans-hardware-buddy`
   - Group email: `nathans-hardware-buddy@yourdomain.com`
   - Privacy settings: `Private`
   - Click "Create"

2. **Configure Document Library**:
   - Navigate to your new SharePoint site
   - Click "Documents" library
   - Create folder: `Knowledge Base`
   - Set permissions for the service account that will upload files

#### Step 3: Power Automate Flow Setup

1. **Access Power Automate**:
   - Navigate to [make.powerautomate.com](https://make.powerautomate.com)
   - Ensure you're in the correct environment (top right)

2. **Import Flow from Template**:
   - Click "My flows" in the left menu
   - Click "Import" → "Import Package (Legacy)"
   - Click "Upload" and select `copilot/power_automate_flow.json`
   - Click "Import"

3. **Configure Connections**:
   - In the import screen, for each connection:
     - Office 365 Outlook:
       - Click "Select during import"
       - Choose existing connection or "Create new"
       - Sign in with pgits@hexalinks.com account
     - SharePoint:
       - Click "Select during import"
       - Choose existing connection or "Create new"
       - Sign in with account that has access to SharePoint site
   - Click "Import"

4. **Update Flow Configuration**:
   - Open the imported flow
   - Click "Edit"
   - Update trigger settings:
     - Folder: `Inbox`
     - From: `do_not_reply@tdsynnex.com`
     - To: `pgits@hexalinks.com`
     - Has Attachments: `Yes`
   - Update SharePoint action:
     - Site Address: `https://yourdomain.sharepoint.com/sites/nathans-hardware-buddy`
     - Folder Path: `/Shared Documents/Knowledge Base`
   - Click "Save"
   - Click "Turn on" to activate the flow

#### Step 4: Copilot Studio Configuration

1. **Access Copilot Studio**:
   - Navigate to [copilotstudio.microsoft.com](https://copilotstudio.microsoft.com)
   - Sign in and ensure you're in the correct environment

2. **Create New Copilot**:
   - Click "+ Create" → "New copilot"
   - Choose "Skip to configure"
   - Name: `Nathan's Hardware Buddy v.1`
   - Description: `Microsoft product specialist with TD SYNNEX inventory`
   - Instructions: `You are a Microsoft product expert with access to real-time TD SYNNEX inventory data. Help users with product availability, pricing, and recommendations.`
   - Click "Create"

3. **Configure Knowledge Sources**:
   - In your copilot, click "Knowledge" in the left menu
   - Click "+ Add knowledge"
   - Choose "SharePoint"
   - SharePoint site: Select your `nathans-hardware-buddy` site
   - Document libraries: Select "Documents"
   - Folders: Select "Knowledge Base" folder
   - File types: Check "Excel files", "CSV files", "Text files"
   - Click "Add"

4. **Configure Data Sources**:
   - Click "Settings" (gear icon) in the left menu
   - Go to "Generative AI" tab
   - Content moderation: `Medium`
   - How strict: `More precise`
   - Web search: `Off` (we'll use our specific data)
   - Click "Save"

5. **Test the Copilot**:
   - Click "Test" in the top right
   - Try sample queries:
     - "What Microsoft Surface devices are available?"
     - "Show me the latest Windows licensing options"
     - "What's the price of Microsoft 365 Business Premium?"

6. **Publish to Teams**:
   - Click "Publish" in the left menu
   - Click "Publish"
   - After publishing, click "Availability options"
   - Enable "Microsoft Teams"
   - Configure Teams app:
     - App name: `Nathan's Hardware Buddy`
     - Short description: `Microsoft product inventory assistant`
     - Long description: `Your go-to assistant for Microsoft product availability, pricing, and recommendations based on real-time TD SYNNEX inventory data.`
   - Click "Submit for approval" or "Publish to my organization"

#### Step 5: Integration Validation

1. **Test Power Automate Flow**:
   - Send a test email to pgits@hexalinks.com with a CSV attachment
   - Subject should contain "Microsoft"
   - Verify the flow triggers and file uploads to SharePoint

2. **Verify SharePoint Integration**:
   - Check that files appear in Knowledge Base folder
   - Confirm Copilot can access the files in responses

3. **Test End-to-End**:
   - Run a manual scraper test
   - Verify email forwarding works
   - Check SharePoint file upload
   - Test Copilot responses with new data

#### Troubleshooting Power Platform Issues

1. **Flow Not Triggering**:
   - Check email trigger conditions
   - Verify pgits@hexalinks.com permissions
   - Review connection authentication

2. **SharePoint Upload Failures**:
   - Verify SharePoint permissions
   - Check folder structure exists
   - Confirm file size limits

3. **Copilot Not Finding Data**:
   - Refresh knowledge sources manually
   - Check indexing status
   - Verify file formats are supported

## Project Structure

```
scraper/
├── src/
│   ├── scraper/           # Core scraping logic
│   ├── models/            # ML models for product classification
│   ├── notifications/     # Email alert system
│   └── config/            # Configuration management
├── copilot/               # Copilot Studio configurations
├── deployment/            # Deployment configurations
│   ├── kubernetes/        # K8s manifests
│   └── azure/             # Azure ARM templates
├── tests/                 # Unit and integration tests
└── requirements.txt       # Python dependencies
```

## Testing

Run the test suite:
```bash
# All tests
pytest

# Specific test modules
pytest tests/test_scraper.py -v
pytest tests/test_classifier.py -v
pytest tests/test_email.py -v

# With coverage
pytest --cov=src tests/
```

## Deployment

### Kubernetes

1. Create namespace and secrets:
```bash
kubectl apply -f deployment/kubernetes/service.yaml
```

2. Update secrets with your credentials:
```bash
kubectl edit secret td-synnex-credentials -n scraper
kubectl edit secret email-credentials -n scraper
```

3. Deploy the application:
```bash
kubectl apply -f deployment/kubernetes/deployment.yaml
```

### Azure Container Instances (Detailed)

#### Option A: Using Azure CLI (Recommended)

1. **Install Azure CLI** (if not already installed):
   ```bash
   # Windows (using Chocolatey)
   choco install azure-cli
   
   # macOS (using Homebrew)
   brew install azure-cli
   
   # Linux (Ubuntu/Debian)
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

2. **Login and Set Subscription**:
   ```bash
   # Login to Azure
   az login
   
   # List subscriptions
   az account list --output table
   
   # Set active subscription
   az account set --subscription "Your Subscription Name"
   
   # Verify current subscription
   az account show
   ```

3. **Create Resource Group**:
   ```bash
   az group create \
     --name rg-td-synnex-scraper \
     --location eastus
   ```

4. **Build and Push Docker Image** (if using custom image):
   ```bash
   # Build the image
   docker build -t td-synnex-scraper:latest -f deployment/Dockerfile .
   
   # Tag for Azure Container Registry
   docker tag td-synnex-scraper:latest tdsynnexscraper.azurecr.io/td-synnex-scraper:latest
   
   # Login to ACR
   az acr login --name tdsynnexscraper
   
   # Push image
   docker push tdsynnexscraper.azurecr.io/td-synnex-scraper:latest
   ```

5. **Deploy Container Instance**:
   ```bash
   az deployment group create \
     --resource-group rg-td-synnex-scraper \
     --template-file deployment/azure/arm_template.json \
     --parameters \
       containerName=td-synnex-scraper \
       imageUri=tdsynnexscraper.azurecr.io/td-synnex-scraper:latest \
       tdSynnexUsername="your_td_synnex_username" \
       tdSynnexPassword="your_td_synnex_password" \
       emailUsername="your_email@domain.com" \
       emailPassword="your_email_app_password"
   ```

6. **Verify Deployment**:
   ```bash
   # Check container status
   az container show \
     --resource-group rg-td-synnex-scraper \
     --name td-synnex-scraper-group \
     --output table
   
   # View logs
   az container logs \
     --resource-group rg-td-synnex-scraper \
     --name td-synnex-scraper-group
   
   # Get IP address
   az container show \
     --resource-group rg-td-synnex-scraper \
     --name td-synnex-scraper-group \
     --query ipAddress.ip \
     --output tsv
   ```

#### Option B: Using Azure Portal

1. **Navigate to Container Instances**:
   - Go to [portal.azure.com](https://portal.azure.com)
   - Search "Container Instances" → Click "Container Instances"
   - Click "+ Create"

2. **Basic Configuration**:
   - **Subscription**: Select your subscription
   - **Resource Group**: Select `rg-td-synnex-scraper`
   - **Container name**: `td-synnex-scraper`
   - **Region**: `East US` (or your preferred region)
   - **Availability zones**: `None`
   - **Image source**: `Other registry`
   - **Image type**: `Public` (or Private if using ACR)
   - **Image**: `tdsynnexscraper.azurecr.io/td-synnex-scraper:latest`
   - **OS type**: `Linux`

3. **Size Configuration**:
   - **Size**: `2 vCPU, 4 GiB memory`
   - Click "Next: Networking >"

4. **Networking Configuration**:
   - **Networking type**: `Public`
   - **DNS name label**: `td-synnex-scraper-{unique-id}`
   - **Ports**: 
     - Port: `8080`
     - Protocol: `TCP`
   - Click "Next: Advanced >"

5. **Advanced Configuration**:
   - **Restart policy**: `On failure`
   - **Environment variables**: Add the following (mark sensitive ones as "Secure"):
     
     | Name | Value | Secure |
     |------|-------|--------|
     | TDSYNNEX_USERNAME | your_username | ✓ |
     | TDSYNNEX_PASSWORD | your_password | ✓ |
     | EMAIL_USERNAME | your_email@domain.com | ✓ |
     | EMAIL_PASSWORD | your_email_password | ✓ |
     | IMAP_SERVER | imap.gmail.com | |
     | SMTP_SERVER | smtp.gmail.com | |
     | SMTP_PORT | 587 | |
     | LOG_LEVEL | INFO | |

   - **Command override**: Leave empty
   - Click "Review + create"

6. **Review and Create**:
   - Review all settings
   - Click "Create"
   - Wait for deployment to complete

#### Post-Deployment Steps

1. **Verify Container Health**:
   - Navigate to your Container Instance
   - Check "Overview" tab shows "Running" status
   - Click "Logs" tab to see application output
   - Look for successful initialization messages

2. **Test Health Endpoint**:
   ```bash
   # Get the public IP
   CONTAINER_IP=$(az container show \
     --resource-group rg-td-synnex-scraper \
     --name td-synnex-scraper-group \
     --query ipAddress.ip \
     --output tsv)
   
   # Test health endpoint
   curl http://$CONTAINER_IP:8080/health
   ```

3. **Set Up Monitoring and Alerts**:
   - In Azure Portal, go to your Container Instance
   - Click "Monitoring" → "Logs"
   - Create log queries for monitoring:
     ```kusto
     ContainerInstanceLog_CL
     | where ContainerGroup_s == "td-synnex-scraper-group"
     | where Message contains "ERROR"
     | order by TimeGenerated desc
     ```
   - Set up alerts for failures
   - Configure email notifications

4. **Configure Log Analytics** (Optional but recommended):
   - Create Log Analytics Workspace
   - Link Container Instance to workspace
   - Set up custom dashboards for monitoring

## Monitoring

- **Logs**: Available in `./logs` directory (local) or container logs
- **Health Check**: HTTP endpoint on port 8080
- **Prometheus Metrics**: Available on port 9090 (when enabled)
- **Email Notifications**: Sent to pgits@hexalinks.com on failures

## Troubleshooting

### Common Issues

1. **Login Failures**:
   - Verify TD SYNNEX credentials
   - Check if portal URL has changed
   - Review browser automation selectors

2. **Email Not Received**:
   - Verify email monitoring credentials
   - Check spam/junk folders
   - Increase timeout in configuration

3. **Product Classification Issues**:
   - Review Microsoft keyword list
   - Check HuggingFace model availability
   - Examine classification confidence scores

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m src.scraper.main
```

## Maintenance

- **Weekly**: Review scraping success rate and logs
- **Monthly**: Update ML models and dependencies
- **Quarterly**: Review Microsoft product filters
- **As Needed**: Update web selectors if TD SYNNEX UI changes

## Security Notes

- Store credentials securely (use environment variables)
- Never commit `.env` file to version control
- Use app-specific passwords for email accounts
- Rotate credentials regularly
- Monitor for unusual activity

## Support

For issues or questions:
- Email: pgits@hexalinks.com
- Check logs for detailed error messages
- Review test suite for expected behavior

## License

[Your License Here]