# TD SYNNEX Knowledge Update Service

A specialized service for automatically retrieving TD SYNNEX price files from email attachments and updating Microsoft Copilot Studio knowledge bases.

## Features

- **Email Attachment Retrieval**: Automatically finds and downloads TD SYNNEX price files from email attachments
- **File Processing**: Handles both `.eml` and `.txt` files with intelligent content extraction
- **Pattern Matching**: Recognizes TD SYNNEX filename patterns (`customernum-MM-DD-unique.txt`)
- **Copilot Studio Integration**: Updates knowledge base via Dataverse API
- **Container Ready**: Optimized for Azure Container Apps deployment
- **RESTful API**: HTTP endpoints for integration and automation

## Quick Start

### Local Development

1. **Clone and Setup**:
   ```bash
   cd knowledge-update
   cp .env.example .env
   # Edit .env with your Azure credentials
   ```

2. **Install Dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run Locally**:
   ```bash
   chmod +x start_knowledge_service.sh
   ./start_knowledge_service.sh
   ```

### Azure Container Deployment

1. **Configure Deployment**:
   ```bash
   # Edit deploy-azure.sh with your Azure settings
   RESOURCE_GROUP="your-resource-group"
   REGISTRY_NAME="your-container-registry"
   ```

2. **Deploy to Azure**:
   ```bash
   chmod +x deploy-azure.sh
   ./deploy-azure.sh all
   ```

## API Endpoints

### Health & Status
- `GET /health` - Health check with connection tests
- `GET /ready` - Readiness probe for containers
- `GET /status` - Service status information

### File Operations
- `GET /latest-attachment` - Get latest TD SYNNEX price file
- `GET /attachment-history` - List historical price files
- `POST /update-knowledge-base` - Update Copilot Studio knowledge

### Integration
- `POST /webhook/power-automate` - Power Automate webhook endpoint

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_TENANT_ID` | ✅ | Azure AD Tenant ID |
| `AZURE_CLIENT_ID` | ✅ | Azure AD App Client ID |
| `AZURE_CLIENT_SECRET` | ✅ | Azure AD App Secret |
| `OUTLOOK_USER_EMAIL` | ✅ | Email account to monitor |
| `CUSTOMER_NUMBER` | ✅ | TD SYNNEX customer number (e.g., 701601) |
| `DATAVERSE_URL` | ✅ | Dataverse environment URL |
| `COPILOT_AGENT_NAME` | ❌ | Copilot agent name (default: "Nate's Hardware Buddy v.1") |
| `PORT` | ❌ | Service port (default: 5000) |

### Azure AD App Registration

The service requires an Azure AD app registration with the following permissions:

1. **Microsoft Graph API**:
   - `Mail.Read` - Read email messages
   - `Mail.ReadWrite` - Access email attachments

2. **Dataverse**:
   - Read/Write permissions to Copilot components table
   - Access to your Dataverse environment

## Usage Examples

### Get Latest Price File
```bash
curl "http://localhost:5000/latest-attachment?max_age_minutes=120&download=true"
```

### Update Knowledge Base
```bash
curl -X POST "http://localhost:5000/update-knowledge-base" \
  -H "Content-Type: application/json" \
  -d '{
    "max_age_minutes": 60,
    "force_update": true
  }'
```

### Check Service Health
```bash
curl "http://localhost:5000/health"
```

## File Processing

### Supported Formats
- **`.txt`** - Direct TD SYNNEX price files
- **`.eml`** - Email files containing `.txt` attachments

### Filename Pattern
The service recognizes TD SYNNEX price files with the pattern:
```
{customer_number}-{MM}-{DD}-{unique_id}.txt
```
Example: `701601-07-21-1627.txt`

### Content Validation
- File size limits (max 512MB for Copilot Studio)
- Content encoding detection (UTF-8, Latin-1)
- Price data format validation

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Email Service   │────│ File Processor  │────│ Copilot Updater │
│                 │    │                 │    │                 │
│ - Graph API     │    │ - .eml parsing  │    │ - Dataverse API │
│ - Attachment    │    │ - Pattern match │    │ - Knowledge mgmt│
│   download      │    │ - Validation    │    │ - File upload   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Container Deployment

### Azure Container Apps (Recommended)
- Automatic scaling based on HTTP requests
- Built-in load balancing
- Container health monitoring
- Easy CI/CD integration

### Azure Container Instances
- Simple single-container deployment
- Good for development/testing
- Fixed resource allocation

### Configuration Files
- `Dockerfile` - Multi-stage build for development
- `Dockerfile.azure` - Optimized for Azure deployment
- `deploy-azure.sh` - Automated deployment script

## Monitoring & Logging

### Health Checks
- Container health probes at `/health`
- Readiness checks at `/ready`
- Connection validation for external services

### Logging
- Structured logging to stdout
- Request/response logging
- Error tracking with context
- Performance metrics

## Security

### Best Practices
- Non-root container user
- Minimal base image (Python slim)
- Credential management via environment variables
- HTTPS-only communication in production

### Network Security
- Private endpoints for Azure services
- Virtual network integration
- Firewall rules for container access

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Check Azure AD app permissions
   - Verify client secret hasn't expired
   - Confirm tenant ID is correct

2. **Email Access Issues**:
   - Ensure Mail.Read permissions granted
   - Check email account exists and is accessible
   - Verify Graph API connectivity

3. **File Processing Errors**:
   - Check filename pattern matches expected format
   - Verify file encoding (UTF-8 preferred)
   - Ensure file size within limits

4. **Copilot Studio Updates**:
   - Confirm Dataverse URL is correct
   - Check app registration has Dataverse permissions
   - Verify agent name matches exactly

### Debug Mode
Set `LOG_LEVEL=DEBUG` in environment for verbose logging.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Azure AD permissions
3. Verify environment configuration
4. Create an issue with detailed logs