# Azure App Registration Setup for Email Verification Service

This guide will help you set up Azure AD App Registration to allow the email verification service to read emails from Outlook using Microsoft Graph API.

## Prerequisites

- Azure AD tenant admin access
- Outlook/Office 365 account (pgits@hexalinks.com)
- Azure CLI or Azure Portal access

## Step 1: Create Azure AD App Registration

### Using Azure Portal:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory**
3. Click on **App registrations**
4. Click **New registration**
5. Fill in the details:
   - **Name**: `TD SYNNEX Email Verification Service`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: Leave blank (not needed for daemon app)
6. Click **Register**

### Using Azure CLI:

```bash
# Create app registration
az ad app create \
  --display-name "TD SYNNEX Email Verification Service" \
  --sign-in-audience "AzureADMyOrg"

# Note down the appId from the output
```

## Step 2: Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Choose **Application permissions** (not Delegated)
5. Add these permissions:
   - `Mail.Read` - Read mail in all mailboxes
   - `User.Read.All` - Read all users' profiles (needed to access specific user's mailbox)

6. Click **Add permissions**
7. **IMPORTANT**: Click **Grant admin consent** for your tenant

### Using Azure CLI:

```bash
# Get the app object ID
APP_ID="your-app-id-here"
APP_OBJECT_ID=$(az ad app show --id $APP_ID --query "id" -o tsv)

# Add Mail.Read permission
az ad app permission add \
  --id $APP_ID \
  --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions 810c84a8-4a9e-49e8-ab7b-3c20eafb5b66=Role

# Add User.Read.All permission  
az ad app permission add \
  --id $APP_ID \
  --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions df021288-bdef-4463-88db-98f22de89214=Role

# Grant admin consent
az ad app permission admin-consent --id $APP_ID
```

## Step 3: Create Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Add description: `Email verification service secret`
4. Choose expiration: `24 months` (or according to your policy)
5. Click **Add**
6. **IMPORTANT**: Copy the secret value immediately (it won't be shown again)

### Using Azure CLI:

```bash
# Create client secret
az ad app credential reset \
  --id $APP_ID \
  --display-name "Email verification service secret" \
  --years 2

# Note down the password from the output
```

## Step 4: Get Required Values

From your app registration, collect these values:

1. **Application (client) ID**: Found in the Overview tab
2. **Directory (tenant) ID**: Found in the Overview tab  
3. **Client secret**: The value you copied in Step 3

## Step 5: Configure Environment Variables

Set these environment variables for your deployment:

```bash
export AZURE_TENANT_ID="your-tenant-id-here"
export AZURE_CLIENT_ID="your-client-id-here"
export AZURE_CLIENT_SECRET="your-client-secret-here"
export OUTLOOK_USER_EMAIL="pgits@hexalinks.com"
```

## Step 6: Test the Setup

### Local Testing:

1. Create a `.env` file in the `email-verification-service` directory:
```
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-here
OUTLOOK_USER_EMAIL=pgits@hexalinks.com
```

2. Run the email service locally:
```bash
cd email-verification-service
python app.py
```

3. Test the endpoints:
```bash
# Health check
curl http://localhost:5000/health

# Test email connection
curl http://localhost:5000/test-email

# Get verification code
curl "http://localhost:5000/verification-code?sender=do_not_reply@tdsynnex.com"
```

### Azure Deployment:

Use the deployment script with the environment variables:

```bash
export AZURE_TENANT_ID="your-tenant-id-here"
export AZURE_CLIENT_ID="your-client-id-here"
export AZURE_CLIENT_SECRET="your-client-secret-here"

./deploy-multi-container-apps.sh "pgits@hexalinks.com" "your-password"
```

## Security Considerations

1. **Least Privilege**: The app only has `Mail.Read` permission, not write access
2. **Scope**: Permissions are limited to the specific mailbox
3. **Secrets**: Store client secrets securely (Azure Key Vault recommended for production)
4. **Monitoring**: Enable auditing for the app registration
5. **Rotation**: Regularly rotate client secrets

## Troubleshooting

### Common Issues:

1. **403 Forbidden**: Admin consent not granted
   - Solution: Go to API permissions and click "Grant admin consent"

2. **401 Unauthorized**: Invalid credentials
   - Solution: Verify tenant ID, client ID, and client secret

3. **No emails found**: Graph API query issues
   - Solution: Check the user email format and permissions

4. **Token expired**: Authentication token issues
   - Solution: The service automatically refreshes tokens

### Verification Steps:

1. Check app registration permissions in Azure Portal
2. Verify admin consent has been granted
3. Test authentication with Microsoft Graph Explorer
4. Check Azure AD audit logs for authentication events

## Production Recommendations

1. Use **Azure Key Vault** to store client secrets
2. Enable **conditional access policies** for the app
3. Set up **monitoring and alerts** for the service
4. Use **managed identities** where possible
5. Implement **proper logging** for audit trails

## Support

If you encounter issues:
1. Check Azure AD audit logs
2. Review application logs in Azure Container Apps
3. Use Microsoft Graph Explorer to test permissions
4. Contact your Azure AD administrator for permission issues