#!/bin/bash

# Repository Setup Script for copilot-refresh-service
# Run this script after creating the repository on GitHub

echo "🚀 Setting up copilot-refresh-service repository..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Prompt for GitHub username
read -p "Enter your GitHub username: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ GitHub username is required"
    exit 1
fi

# Repository URL
REPO_URL="https://github.com/$GITHUB_USERNAME/copilot-refresh-service.git"

echo "📂 Repository URL: $REPO_URL"

# Create a temporary directory for setup
SETUP_DIR="/tmp/copilot-refresh-service-setup"
rm -rf "$SETUP_DIR"
mkdir -p "$SETUP_DIR"

echo "📥 Cloning repository..."
if git clone "$REPO_URL" "$SETUP_DIR"; then
    echo "✅ Repository cloned successfully"
else
    echo "❌ Failed to clone repository. Please check:"
    echo "   1. Repository exists at: $REPO_URL"
    echo "   2. You have access to the repository"
    echo "   3. GitHub credentials are set up correctly"
    exit 1
fi

# Navigate to the repository
cd "$SETUP_DIR"

echo "📁 Copying deployment files..."
# Copy all files from current azure-deployment directory
cp -r /Users/petergits/dev/claude-orchestra/scraper/refresh-rag-service/azure-deployment/* .

# Remove any nested .git directories
find . -name ".git" -type d -not -path "./.git" -exec rm -rf {} + 2>/dev/null || true

# Create a proper README.md
cat > README.md << 'EOF'
# Copilot Refresh Service

Automated service for uploading ec-synnex files to Copilot Studio via SharePoint monitoring.

## Overview

This service monitors a SharePoint folder for new ec-synnex Excel files and automatically uploads them to a Copilot Studio agent's knowledge base, replacing existing files.

## Features

- **SharePoint Monitoring**: Automatically detects new files in SharePoint
- **Copilot Studio Integration**: Updates knowledge base via REST API
- **Azure Container Apps**: Scalable cloud deployment
- **Managed Identity**: Secure authentication without credentials
- **Application Insights**: Comprehensive monitoring and logging
- **GitHub Actions**: Automated CI/CD pipeline

## Quick Start

1. **Azure Infrastructure**: Already deployed in `rg-copilot-refresh`
2. **SharePoint Setup**: Files uploaded to `https://hexalinks.sharepoint.com/sites/QuotationsTeam`
3. **Container Deployment**: Automated via GitHub Actions

## Architecture

```
SharePoint → Azure Container App → Copilot Studio
     ↓              ↓                    ↓
File Upload → Processing Service → Knowledge Update
```

## Configuration

- **Agent ID**: `e71b63c6-9653-f011-877a-000d3a593ad6`
- **Environment**: `33a7afba-68df-4fb5-84ba-abd928569b69`
- **SharePoint Site**: QuotationsTeam
- **Target Folder**: EC Synnex Files

## Deployment

See `COMPLETE_DEPLOYMENT_MANUAL.md` for detailed instructions.

## File Upload Process

1. Upload `ec-synnex-*.xls` files to SharePoint
2. Service detects new files within 5 minutes
3. Files are processed and uploaded to Copilot Studio
4. Original files are moved to `Processed` folder
5. Knowledge base is updated automatically

## Monitoring

- **Health Check**: `https://YOUR_APP_URL/health`
- **Application Insights**: Monitor performance and errors
- **Container Logs**: Real-time application logging

## Documentation

- `COMPLETE_DEPLOYMENT_MANUAL.md` - Complete setup and deployment guide
- `GITHUB_ACTIONS_SETUP.md` - GitHub Actions configuration
- `ADMIN_SETUP_REQUIRED.md` - Admin permissions and setup
- `docs/hexalinks-sharepoint-setup.md` - SharePoint configuration

## Support

For issues and troubleshooting, see the documentation files in this repository.
EOF

echo "📝 Adding files to git..."
git add .

echo "💾 Committing changes..."
git commit -m "Initial deployment setup with GitHub Actions workflow

Features:
- Container build and deployment workflow
- Azure infrastructure configuration  
- SharePoint monitoring service
- Copilot Studio integration
- Comprehensive documentation and setup guides
- Health monitoring and logging

Infrastructure:
- Azure Container Registry: copilotrefreshacr597769.azurecr.io
- Container App: copilot-refresh-app
- Resource Group: rg-copilot-refresh
- SharePoint: https://hexalinks.sharepoint.com/sites/QuotationsTeam"

echo "🚀 Pushing to GitHub..."
if git push origin main; then
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🎉 Repository setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. 👨‍💼 Get admin help to create service principal (see ADMIN_SETUP_REQUIRED.md)"
    echo "2. 🔑 Configure GitHub secrets (see GITHUB_ACTIONS_SETUP.md)"
    echo "3. 🚀 Run GitHub Actions workflow to deploy"
    echo "4. 📋 Test by uploading files to SharePoint"
    echo ""
    echo "Repository URL: $REPO_URL"
    echo "Actions URL: $REPO_URL/actions"
else
    echo "❌ Failed to push to GitHub. Please check your credentials and try again."
    exit 1
fi

# Clean up
cd /
rm -rf "$SETUP_DIR"

echo "✨ Setup complete! Check your repository at: $REPO_URL"