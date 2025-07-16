# Hexalinks SharePoint Setup

## Using Existing SharePoint Site

The solution has been configured to use the existing Hexalinks SharePoint site instead of creating a new one.

### SharePoint Configuration

- **Tenant:** hexalinks
- **Site URL:** https://hexalinks.sharepoint.com/sites/QuotationsTeam
- **Library:** Shared Documents
- **Folder:** EC Synnex Files
- **Site Link:** https://hexalinks.sharepoint.com/sites/QuotationsTeam/Shared%20Documents/Forms/AllItems.aspx

### Prerequisites

1. **Access to Hexalinks SharePoint:** You need access to the Hexalinks SharePoint site
2. **Folder Access:** Verify you can access the "EC Synnex Files" folder
3. **Upload Permissions:** Ensure you can upload files to the folder

### Verification Steps

#### Step 1: Test SharePoint Access

```bash
# Open the SharePoint site in your browser
open "https://hexalinks.sharepoint.com/sites/QuotationsTeam/Shared%20Documents/Forms/AllItems.aspx"
```

#### Step 2: Verify Folder Structure

Navigate to the SharePoint site and verify this folder structure exists:
```
QuotationsTeam/
├── Shared Documents/
│   └── EC Synnex Files/           # This is where files will be uploaded
│       ├── [Your ec-synnex files here]
│       └── Processed/             # Will be created automatically
└── [Other folders...]
```

#### Step 3: Test File Upload

1. Go to the EC Synnex Files folder
2. Upload a test file named `test-ec-synnex-sample.xls`
3. Verify the file appears in the folder
4. Delete the test file

### Folder Creation (If Needed)

If the "EC Synnex Files" folder doesn't exist, create it:

1. Navigate to the Shared Documents library
2. Click "New" → "Folder"
3. Name it "EC Synnex Files"
4. Click "Create"

### Permissions Setup

The Azure Managed Identity will need permissions to access this SharePoint site. This is handled automatically during deployment, but you may need to:

1. **Grant site access** to the managed identity
2. **Configure API permissions** in Azure Portal (covered in deployment guide)

### File Processing Workflow

1. **Upload Location:** Files uploaded to `/Shared Documents/EC Synnex Files/`
2. **Pattern Matching:** Only files starting with `ec-synnex-` are processed
3. **File Types:** Only `.xls` and `.xlsx` files are supported
4. **Processing:** Files are automatically moved to `Processed/` folder after upload
5. **Naming:** Processed files are renamed with timestamp prefix

### Troubleshooting

#### Issue: Cannot access SharePoint folder
**Solution:** 
- Verify you're signed in to the correct Microsoft 365 account
- Check that you have access to the Hexalinks tenant
- Contact your SharePoint administrator for access

#### Issue: Folder doesn't exist
**Solution:**
- Create the "EC Synnex Files" folder in the Documents library
- Ensure the folder name matches exactly (case-sensitive)

#### Issue: Cannot upload files
**Solution:**
- Check you have "Contribute" or "Full Control" permissions
- Verify the file size is under 512MB
- Ensure the file name starts with "ec-synnex-"

### Manual File Upload Process

While the automated system is being set up, you can manually upload files:

1. **Go to SharePoint:** https://hexalinks.sharepoint.com/sites/QuotationsTeam
2. **Navigate to Shared Documents** → **EC Synnex Files**
3. **Upload your file:** `ec-synnex-701601-0708-0927.xls`
4. **Wait for processing:** The container will pick it up within 5 minutes
5. **Check Copilot Studio:** Verify the file appears in the knowledge base

### Container Configuration

The container is configured with these SharePoint settings:

```bash
SHAREPOINT_SITE_URL=https://hexalinks.sharepoint.com/sites/QuotationsTeam
SHAREPOINT_LIBRARY_NAME=Shared Documents
SHAREPOINT_FOLDER_PATH=EC Synnex Files
SHAREPOINT_TENANT=hexalinks
```

### Security Considerations

- **Managed Identity:** The Azure container uses a managed identity to access SharePoint
- **Minimal Permissions:** Only read/write access to the specific folder
- **Audit Trail:** All file operations are logged in Application Insights
- **No Credentials:** No usernames or passwords are stored in the container

### Next Steps

Once you've verified SharePoint access:

1. ✅ Confirm folder access and upload permissions
2. ✅ Proceed with Azure deployment: `./scripts/deploy-infrastructure.sh -g "rg-copilot-refresh"`
3. ✅ Test the automated upload process
4. ✅ Monitor container logs for successful processing

The solution is now configured to work with your existing Hexalinks SharePoint infrastructure without requiring any new site creation.