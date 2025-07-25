# Application User Setup for Dataverse Access

## Method: Create Application User in Power Platform Admin Center

This bypasses the Azure AD permission issue by directly registering your app in Dataverse.

### Steps:

1. **Go to Power Platform Admin Center**:
   - Visit: https://admin.powerplatform.microsoft.com
   - Sign in with admin account

2. **Select Your Environment**:
   - Click "Environments"
   - Select the environment with your Copilot Studio agent
   - This should be: `Default-33a7afba-68df-4fb5-84ba-abd928569b69`

3. **Navigate to Users**:
   - In the environment details, click "Settings"
   - Under "Users + permissions", click "Application users"

4. **Create New Application User**:
   - Click "+ New app user"
   - Click "+ Add an app"

5. **Register Your Azure App**:
   - Search for your app using Client ID: `99bfa715-5285-4904-812a-99af4937dab6`
   - If not found, click "Create a new app registration" and use your existing app details
   - Select your app and click "Add"

6. **Assign Security Roles**:
   - In "Business unit", select the root business unit
   - In "Security roles", add:
     - **System Administrator** (for testing)
     - **System Customizer** (minimum needed)
   - Click "Create"

### Benefits:
- No need to find missing Dataverse permissions in Azure AD
- Direct access to Dataverse environment
- Proper security role assignment
- Works even when API permissions aren't visible

### Security Roles Needed:
- **System Customizer**: Read/write access to customizations
- **Basic User**: Basic Dataverse access
- **System Administrator**: Full access (use carefully)