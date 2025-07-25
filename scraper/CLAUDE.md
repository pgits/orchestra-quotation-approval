## Development Notes

- Use uv instead of pip
- Remember that deploy-azure-enhanced tries to use the platform in azure with linux/amd64
- When there's a platform architecture issue, the Azure Container Apps needs a linux/amd64 image, locally I built an ARM64 image on my Mac. Rebuild for the correct platform.

## Main Services

- `./start_td_synnex_system.sh` - Main TD SYNNEX scraper system
- `./email-verification-service/start_email_service.sh` - Email 2FA service
- `./knowledge-update/start_knowledge_update_service.sh` - Knowledge update service
- `./start_screenshot_viewer.sh` - Screenshot monitoring
- `./start_2fa_api.sh` - 2FA API service