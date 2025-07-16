# Simple Solution - Multiple Approaches

I've created multiple approaches since Power Automate package import can be finicky. Choose the one that works best for you:

## Approach 1: Fixed Package Import ✅

The package structure has been corrected. Try importing again:

```bash
# The corrected package is already created at:
flows/CopilotKnowledgeRefreshFlow.zip
```

**Steps:**
1. Go to https://powerautomate.microsoft.com
2. Click "My flows" → "Import" → "Import Package (Legacy)"
3. Upload: `flows/CopilotKnowledgeRefreshFlow.zip`
4. Configure connections when prompted
5. Set the Agent ID parameter

## Approach 2: Direct Dataverse Upload (No Power Automate) 🚀

This completely bypasses Power Automate and uploads directly to Dataverse:

```bash
# Install required library
pip3 install --user msal

# Upload directly
python3 scripts/direct-dataverse-upload.py ~/Downloads/ec-synnex-701601-0708-0927.xls
```

**Advantages:**
- No Power Automate flow needed
- Direct API calls to Dataverse
- More reliable and faster
- Handles authentication automatically

## Approach 3: Manual Flow Creation 📝

If package import still fails, create manually:

```bash
cat docs/manual-flow-creation.md
```

Follow the step-by-step guide to build the flow in the web interface.

## Quick Setup for Direct Upload

1. **Configure your Agent ID:**
   ```bash
   python3 scripts/config-wizard.py
   ```

2. **Install authentication library:**
   ```bash
   pip3 install --user msal
   ```

3. **Upload your file:**
   ```bash
   python3 scripts/direct-dataverse-upload.py ~/Downloads/ec-synnex-701601-0708-0927.xls
   ```

## Finding Your Agent ID

1. Go to https://copilotstudio.microsoft.com
2. Find "Nathan's Hardware Buddy v.1"
3. Click on the agent
4. Copy the Agent ID from the URL:
   `https://copilotstudio.microsoft.com/environments/ENV_ID/bots/AGENT_ID/...`

## Configuration Example

Update `config/config.json`:

```json
{
  "copilotStudio": {
    "agentId": "12345678-1234-1234-1234-123456789012"
  },
  "dataverse": {
    "url": "https://service.powerapps.com/api/data/v9.2"
  }
}
```

## Recommendation

**Start with Approach 2 (Direct Dataverse Upload)** - it's the most reliable:

1. `pip3 install --user msal`
2. `python3 scripts/config-wizard.py`
3. `python3 scripts/direct-dataverse-upload.py ~/Downloads/ec-synnex-701601-0708-0927.xls`

This approach:
- ✅ No package import issues
- ✅ No Power Automate flow setup
- ✅ Direct API access
- ✅ Automatic authentication
- ✅ Handles file replacement automatically

## Automation

Once working, you can automate with cron:

```bash
# Add to crontab (crontab -e)
0 9 * * * cd /path/to/refresh-rag-service && python3 scripts/direct-dataverse-upload.py ~/Downloads/ec-synnex-701601-0708-0927.xls
```