# Enhanced SharePoint Upload Features

## 🚀 New Functionality Added

I've successfully enhanced the TD SYNNEX Knowledge Update Service with advanced SharePoint upload functionality that addresses your requirements:

### ✨ Key Enhancements

1. **Smart Duplicate Handling** - Automatic filename conflict resolution with incremental numbering
2. **Automatic Previous File Deletion** - Removes the prior TD SYNNEX file after successful upload
3. **Configurable Behavior** - Full control over deletion and naming behavior via API parameters

---

## 🔧 Technical Implementation

### 1. Smart File Naming with Incremental Numbers

**Function:** `_generate_unique_filename()`

```python
# Example behavior:
# If "701601-07-25-1234.txt" exists:
# New file "701601-07-25-1234.txt" becomes "701601-07-25-1234-1.txt"
# Next one becomes "701601-07-25-1234-2.txt", etc.
```

**Features:**
- ✅ Checks existing SharePoint files before upload
- ✅ Automatically adds `-{number}` suffix for duplicates
- ✅ Finds next available number (e.g., -1, -2, -3)
- ✅ Fallback to timestamp if >1000 conflicts (safety measure)
- ✅ Preserves original filename when no conflicts exist

### 2. Automatic Previous File Deletion

**Function:** `_delete_previous_td_synnex_file()`

```python
# Behavior:
# 1. Lists all existing 701601-*.txt files
# 2. Excludes the newly uploaded file
# 3. Finds the most recent previous file (by modification date)
# 4. Deletes only that one file
# 5. Keeps the newly uploaded file safe
```

**Smart Logic:**
- ✅ Only deletes TD SYNNEX files (701601-*.txt pattern)
- ✅ Excludes the file just uploaded
- ✅ Deletes only the most recent previous file
- ✅ Comprehensive error handling and logging
- ✅ Detailed results reporting

### 3. Enhanced Upload Method

**Updated:** `upload_file()` method with new parameters

```python
def upload_file(filename, content, overwrite=True, delete_previous=True):
    # New workflow:
    # 1. Get existing files list
    # 2. Generate unique filename if conflicts exist
    # 3. Upload file with unique name
    # 4. Delete previous TD SYNNEX file (if enabled)
    # 5. Return comprehensive results
```

---

## 🌐 API Enhancements

### Enhanced Query Parameters

#### `/latest-attachment` Endpoint
```bash
# New parameter added:
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/latest-attachment?ignore_time_window=true&download=true&upload_sharepoint=true&delete_previous=true"
```

**Parameters:**
- `delete_previous=true/false` - Delete previous TD SYNNEX file after upload (default: `true`)

#### `/upload-to-sharepoint` Endpoint  
```bash
# Enhanced JSON payload:
curl -X POST "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/upload-to-sharepoint" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "701601-0722-1234.txt",
    "overwrite": true,
    "cleanup_old": false,
    "delete_previous": true,  // NEW: Controls automatic previous file deletion
    "max_age_minutes": 60
  }'
```

**New Parameter:**
- `delete_previous`: Boolean (default: `true`) - Automatically delete the previous TD SYNNEX file after successful upload

---

## 📊 Enhanced Response Format

### Upload Response Structure
```json
{
  "success": true,
  "original_filename": "701601-0722-1234.txt",
  "final_filename": "701601-0722-1234-1.txt",  // NEW: Shows resolved filename
  "file_size": 87049,
  "timestamp": "2025-07-25T16:00:00.000Z",
  "sharepoint_url": "https://hexalinks.sharepoint.com/sites/QuotationsTeam/...",
  "file_id": "01RREGFUYTDY75KDX5XJAIEPDKXEG72N6N",
  "download_url": "https://hexalinks.sharepoint.com/...",
  "delete_previous_result": {  // NEW: Deletion results
    "success": true,
    "deleted_files": ["701601-0722-1220-1753457053.txt"],
    "message": "Successfully deleted previous file: 701601-0722-1220-1753457053.txt"
  }
}
```

### Key Response Fields
- `original_filename`: The filename you requested
- `final_filename`: The actual filename used (with incremental number if needed)
- `delete_previous_result`: Complete information about the automatic cleanup

---

## 🎯 Usage Examples

### Example 1: Automatic Upload with Cleanup (Recommended)
```bash
# Upload latest TD SYNNEX file with automatic previous file deletion
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/latest-attachment?ignore_time_window=true&download=true&upload_sharepoint=true&delete_previous=true"
```

**Result:**
- ✅ Finds latest TD SYNNEX email attachment
- ✅ Downloads and processes the file
- ✅ Uploads with unique filename if needed (e.g., `-1.txt` suffix)
- ✅ Automatically deletes the previous TD SYNNEX file
- ✅ Returns comprehensive results

### Example 2: Manual Upload with Custom Control
```bash
# Upload specific file with custom deletion behavior
curl -X POST "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/upload-to-sharepoint" \
  -H "Content-Type: application/json" \
  -d '{
    "delete_previous": true,
    "cleanup_old": false
  }'
```

### Example 3: Upload Without Deletion (Preserve All Files)
```bash
# Upload but keep all existing files
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/latest-attachment?ignore_time_window=true&download=true&upload_sharepoint=true&delete_previous=false"
```

---

## 🔄 Workflow Comparison

### Before Enhancement
```
1. Upload file to SharePoint
2. File conflicts cause overwrites or errors
3. Old files accumulate over time
4. Manual cleanup required
```

### After Enhancement  
```
1. Check existing files
2. Generate unique filename if conflicts exist (e.g., add -1, -2, etc.)
3. Upload file with unique name
4. Automatically delete the previous TD SYNNEX file
5. Return detailed results including cleanup status
```

---

## 🛡️ Safety Features

### Conflict Prevention
- ✅ **No overwrites**: Files get unique names instead of being overwritten
- ✅ **Smart numbering**: Incremental numbering prevents any data loss
- ✅ **Pattern matching**: Only affects TD SYNNEX files (701601-*.txt)

### Deletion Safety
- ✅ **Targeted deletion**: Only deletes the single most recent previous file
- ✅ **Never deletes current**: The newly uploaded file is always protected
- ✅ **Pattern verification**: Only deletes files matching TD SYNNEX pattern
- ✅ **Error handling**: Failed deletions don't affect upload success

### Logging & Monitoring
- ✅ **Comprehensive logging**: Every action is logged with emojis for clarity
- ✅ **Detailed responses**: Full information about naming and deletion actions
- ✅ **Error reporting**: Clear error messages for troubleshooting

---

## 🚀 Deployment Status

### ✅ **DEPLOYED TO AZURE**
- **Service URL**: `https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io`
- **Status**: Enhanced functionality is live and ready
- **Version**: Latest with smart naming and automatic cleanup

### Testing Commands
```bash
# Health check with enhanced functionality
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/health"

# List current SharePoint files
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/sharepoint-files"

# Test enhanced upload (when new attachment is available)
curl "https://td-synnex-knowledge-update.calmglacier-2bbf2a81.eastus.azurecontainerapps.io/latest-attachment?ignore_time_window=true&download=true&upload_sharepoint=true&delete_previous=true"
```

---

## 📈 Benefits Summary

### Operational Benefits
- **🎯 Zero Data Loss**: Smart naming prevents any file overwrites
- **🧹 Automatic Cleanup**: No manual intervention needed for old file removal
- **⚡ Simplified Workflow**: One command handles everything automatically
- **🔍 Full Visibility**: Detailed logging and response information

### Technical Benefits  
- **🛡️ Conflict Resolution**: Automatic handling of duplicate filenames
- **📊 Comprehensive Reporting**: Detailed results for every operation
- **🔧 Configurable Behavior**: Full control via API parameters
- **⚙️ Backward Compatible**: Existing integrations continue to work

### Business Benefits
- **💰 Reduced Manual Work**: Eliminates need for manual file management
- **📋 Audit Trail**: Complete logging of all file operations
- **🚀 Improved Reliability**: Automated processes reduce human error
- **📈 Scalable Solution**: Handles high-frequency uploads automatically

---

**🎉 The enhanced SharePoint upload functionality is now live and provides exactly what you requested: smart duplicate handling with incremental numbering and automatic deletion of the previous TD SYNNEX file after each successful upload!**

*Enhanced functionality deployed: 2025-07-25*