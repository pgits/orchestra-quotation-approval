# Repository Setup Instructions

## Step 1: Create the Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `copilot-refresh-service`
3. Description: `Automated service for uploading ec-synnex files to Copilot Studio via SharePoint monitoring`
4. Set to Private
5. Initialize with README
6. Add .gitignore: Python
7. Click "Create repository"

## Step 2: Clone and Set Up Locally

After creating the repository, GitHub will show you the clone URL. Use it in these commands:

```bash
# Clone the repository (replace YOUR_USERNAME with your GitHub username)
git clone https://github.com/YOUR_USERNAME/copilot-refresh-service.git

# Navigate to the repository
cd copilot-refresh-service

# Copy all the deployment files
cp -r /Users/petergits/dev/claude-orchestra/scraper/refresh-rag-service/azure-deployment/* .

# Remove any existing .git folder from the copied files (if any)
find . -name ".git" -type d -exec rm -rf {} +

# Add all files to git
git add .

# Commit the files
git commit -m "Initial deployment setup with GitHub Actions workflow

- Added container build and deployment workflow
- Added Azure infrastructure configuration
- Added SharePoint monitoring service
- Added comprehensive documentation and setup guides"

# Push to GitHub
git push origin main
```

## Step 3: Verify File Structure

After pushing, your repository should have this structure:

```
copilot-refresh-service/
├── .github/
│   └── workflows/
│       └── build-and-deploy.yml          # GitHub Actions workflow
├── container/
│   ├── Dockerfile                        # Container definition
│   ├── app/
│   │   ├── main.py                       # Main application
│   │   ├── sharepoint_monitor.py         # SharePoint monitoring
│   │   ├── copilot_uploader.py          # Copilot Studio integration
│   │   ├── health_server.py             # Health check server
│   │   └── requirements.txt             # Python dependencies
│   ├── supervisord.conf                  # Process management
│   └── healthcheck.sh                    # Health check script
├── infrastructure/
│   └── bicep/
│       └── main.bicep                    # Azure infrastructure
├── scripts/
│   ├── deploy-infrastructure.sh          # Infrastructure deployment
│   ├── deploy-simple.sh                 # Simplified deployment
│   └── deploy-container-app.sh          # Container app deployment
├── docs/
│   └── hexalinks-sharepoint-setup.md    # SharePoint setup guide
├── config/
│   └── hexalinks-config.json            # Configuration
├── deployment-info.json                 # Deployment information
├── GITHUB_ACTIONS_SETUP.md              # GitHub Actions setup guide
├── ADMIN_SETUP_REQUIRED.md              # Admin instructions
├── COMPLETE_DEPLOYMENT_MANUAL.md        # Complete manual
├── DEPLOYMENT_COMPLETE.md               # Current status
├── UPDATE_SUMMARY.md                    # Update summary
└── README.md                            # Repository README
```

## Step 4: Set Up GitHub Actions

1. Go to your repository on GitHub
2. Click on "Settings" tab
3. Go to "Secrets and variables" → "Actions"
4. Click "New repository secret"
5. Add each secret from the table below:

### Required Secrets

| Secret Name | Value | Notes |
|-------------|-------|-------|
| `AZURE_CREDENTIALS` | *(Need admin help)* | Service principal JSON from admin |
| `COPILOT_AGENT_ID` | `e71b63c6-9653-f011-877a-000d3a593ad6` | Your Copilot Studio agent ID |
| `COPILOT_ENVIRONMENT_ID` | `33a7afba-68df-4fb5-84ba-abd928569b69` | Your environment ID |
| `SHAREPOINT_SITE_URL` | `https://hexalinks.sharepoint.com/sites/QuotationsTeam` | SharePoint site URL |
| `SHAREPOINT_LIBRARY_NAME` | `Shared Documents` | SharePoint library name |
| `SHAREPOINT_FOLDER_PATH` | `EC Synnex Files` | SharePoint folder path |
| `SHAREPOINT_TENANT` | `hexalinks` | SharePoint tenant |
| `APPINSIGHTS_INSTRUMENTATION_KEY` | `37d88369-a344-4309-8040-e3bd4de4218f` | Application Insights key |
| `AZURE_CLIENT_ID` | `8cb37433-9611-4b2c-95c5-873c7946fc84` | Managed identity client ID |

## Step 5: Get Admin Help

1. Share `ADMIN_SETUP_REQUIRED.md` with your Azure AD administrator
2. They need to create a service principal and provide you with the JSON credentials
3. Add the JSON as the `AZURE_CREDENTIALS` secret

## Step 6: Deploy

Once all secrets are configured:

1. Go to "Actions" tab in your repository
2. Click "Build and Deploy Copilot Refresh Service"
3. Click "Run workflow" → "Run workflow"
4. Monitor the deployment progress

## Troubleshooting

- **Permission errors**: Check that admin created the service principal correctly
- **Build failures**: Check the Actions logs for detailed error messages
- **Deployment issues**: Verify all secrets are correctly set

## Next Steps

After successful deployment:
1. Test the health endpoint
2. Upload a test file to SharePoint
3. Monitor the application logs
4. Verify Copilot Studio integration

## Support

For issues:
- Check the `COMPLETE_DEPLOYMENT_MANUAL.md` for comprehensive troubleshooting
- Review GitHub Actions logs for build/deployment errors
- Use Azure Container App logs for runtime issues