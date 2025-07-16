# Copilot Studio Knowledge Base Refresh Service

Automates the process of updating knowledge base files in your Copilot Studio agent "Nathan's Hardware Buddy v.1" using Power Automate flows.

## Quick Start

1. **Setup**: `./scripts/setup-macos.sh`
2. **Get Agent ID**: `./scripts/get-agent-id.sh -AgentName "Nathan's Hardware Buddy v.1"`
3. **Configure**: Edit `config/config.json` with your settings
4. **Deploy**: `./scripts/deploy-flow.sh -EnvironmentId "YOUR_ENV_ID" -SubscriptionId "YOUR_SUB_ID" -ResourceGroupName "YOUR_RG"`
5. **Upload**: `./scripts/upload-file.sh ~/Downloads/ec-synnex-701601-0708-0927.xls`

## Features

- ✅ Automated file replacement (replaces existing `ec-synnex-*` files)
- ✅ macOS native support
- ✅ Power Automate integration
- ✅ File validation and size checking
- ✅ Audit trail and logging
- ✅ Cron job support for automation

## Requirements

- macOS 14+
- Microsoft 365 with Power Automate access
- Copilot Studio agent access
- Dataverse and OneDrive for Business

## Documentation

See [setup-instructions.md](docs/setup-instructions.md) for detailed setup and usage instructions.

## Support

- Power Platform CLI: https://docs.microsoft.com/en-us/power-platform/developer/cli/
- Power Automate: https://docs.microsoft.com/en-us/power-automate/
- Copilot Studio: https://docs.microsoft.com/en-us/microsoft-copilot-studio/