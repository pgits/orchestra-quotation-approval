# Azure Deployment for Copilot Studio Knowledge Refresh

This solution deploys a containerized service in Azure that monitors SharePoint for new ec-synnex files and automatically uploads them to your Copilot Studio agent.

## Overview

- **SharePoint Site**: Hexalinks Quotations Team - Uses existing site with proper permissions
- **Azure Container Instance**: Monitors SharePoint and uploads files
- **Managed Identity**: Handles authentication without credentials
- **Copilot Studio Integration**: Updates knowledge base automatically

## Prerequisites

- Azure subscription with owner/contributor access
- Microsoft 365 admin access (for SharePoint site creation)
- Azure CLI installed on your machine
- Docker Desktop (for local testing)

## Architecture

```
SharePoint Site → Azure Container Instance → Copilot Studio Agent
     ↓                      ↓                        ↓
Hexalinks Quotations → Managed Identity Auth → Nathan's Hardware Buddy v.1
```

## Quick Start

1. **Verify SharePoint Access**: Follow `docs/hexalinks-sharepoint-setup.md`
2. **Deploy Infrastructure**: Run `scripts/deploy-infrastructure.sh -g "rg-copilot-refresh"`
3. **Build & Deploy Container**: Run `scripts/deploy-container.sh`
4. **Test Upload**: Upload a file to SharePoint and verify

## File Structure

```
azure-deployment/
├── README.md                           # This file
├── container/
│   ├── Dockerfile                      # Container definition
│   ├── app/
│   │   ├── main.py                     # Main application
│   │   ├── sharepoint_monitor.py       # SharePoint file monitoring
│   │   ├── copilot_uploader.py         # Copilot Studio upload logic
│   │   └── requirements.txt            # Python dependencies
├── infrastructure/
│   ├── bicep/
│   │   ├── main.bicep                  # Azure infrastructure as code
│   │   ├── container-registry.bicep    # Container registry
│   │   └── managed-identity.bicep      # Managed identity setup
│   └── terraform/                      # Terraform alternative (optional)
├── scripts/
│   ├── deploy-infrastructure.sh        # Deploy Azure resources
│   ├── deploy-container.sh             # Build and deploy container
│   ├── setup-permissions.sh            # Configure permissions
│   └── test-deployment.sh              # Test the deployment
└── docs/
    ├── hexalinks-sharepoint-setup.md    # Hexalinks SharePoint configuration
    ├── deployment-guide.md              # Step-by-step deployment
    └── troubleshooting.md               # Common issues and solutions
```

## Next Steps

1. Verify SharePoint access: `docs/hexalinks-sharepoint-setup.md`
2. Review the deployment guide: `docs/deployment-guide.md`
3. Run the deployment scripts in order