# Manual Power Automate Flow Creation

Since package import can be tricky, here's how to create the flow manually in the Power Automate web interface.

## Step 1: Create New Flow

1. Go to https://powerautomate.microsoft.com
2. Click "Create" → "Instant cloud flow"
3. Name: "Copilot Knowledge Refresh Flow"
4. Trigger: "When an HTTP request is received"
5. Click "Create"

## Step 2: Configure HTTP Trigger

1. Click on the "When an HTTP request is received" trigger
2. Set the **Request Body JSON Schema**:

```json
{
    "type": "object",
    "properties": {
        "FilePath": {
            "type": "string",
            "description": "Path to the file in OneDrive"
        },
        "FileName": {
            "type": "string", 
            "description": "Name of the file to upload"
        }
    },
    "required": [
        "FilePath",
        "FileName"
    ]
}
```

## Step 3: Add Variables

Add these actions in order:

### 3.1 Initialize Agent ID Variable
- Action: "Initialize variable"
- Name: `AgentID`
- Type: `String`
- Value: `YOUR_AGENT_ID_HERE` (replace with actual Agent ID)

### 3.2 Initialize File Pattern Variable
- Action: "Initialize variable"
- Name: `FilePattern`
- Type: `String`
- Value: `ec-synnex-`

## Step 4: List Existing Files

- Action: "List rows" (Dataverse)
- Table name: `Copilot components`
- Filter rows: `contains(msdyn_name, variables('FilePattern')) and _msdyn_parentcopilotcomponentid_value eq variables('AgentID')`
- Select columns: `msdyn_copilotcomponentid,msdyn_name,msdyn_componenttype`

## Step 5: Delete Existing Files

- Action: "Condition"
- Condition: `length(outputs('List_rows')?['body/value'])` is greater than `0`

### If Yes Branch:
- Action: "Apply to each"
- Select output: `value` (from List rows)
- Inside loop:
  - Action: "Delete row" (Dataverse)
  - Table name: `Copilot components`
  - Row ID: `items('Apply_to_each')?['msdyn_copilotcomponentid']`

## Step 6: Get File Content

- Action: "Get file content" (OneDrive for Business)
- File: `triggerBody()?['FilePath']`

## Step 7: Create New Knowledge Component

- Action: "Add a new row" (Dataverse)
- Table name: `Copilot components`
- Set these fields:
  - **Name**: `triggerBody()?['FileName']`
  - **Component Type**: `192350002`
  - **Parent Copilot Component**: `variables('AgentID')`
  - **Knowledge Source Type**: `192350000`
  - **Knowledge Source Subtype**: `192350001`
  - **Component State**: `192350000`
  - **File Content**: `base64(outputs('Get_file_content')?['body'])`
  - **File Extension**: `split(triggerBody()?['FileName'], '.')[1]`
  - **File Size**: `length(outputs('Get_file_content')?['body'])`

## Step 8: Wait for Processing

- Action: "Delay"
- Duration: `30` seconds

## Step 9: Check Status

- Action: "Get row by ID" (Dataverse)
- Table name: `Copilot components`
- Row ID: `outputs('Add_a_new_row')?['body/msdyn_copilotcomponentid']`

## Step 10: Return Response

- Action: "Response"
- Status code: `200`
- Body:
```json
{
    "message": "Knowledge base file updated successfully",
    "fileName": "@{triggerBody()?['FileName']}",
    "componentId": "@{outputs('Add_a_new_row')?['body/msdyn_copilotcomponentid']}",
    "status": "completed",
    "timestamp": "@{utcnow()}"
}
```

## Step 11: Save and Test

1. Click "Save"
2. Copy the **HTTP POST URL** from the trigger
3. Update your `config.json` with this URL
4. Test with: `python3 scripts/upload-to-copilot.py ~/Downloads/ec-synnex-701601-0708-0927.xls`

## Finding Your Agent ID

1. Go to https://copilotstudio.microsoft.com
2. Find "Nathan's Hardware Buddy v.1"
3. Click on the agent
4. The Agent ID is in the URL: `https://copilotstudio.microsoft.com/environments/ENVIRONMENT_ID/bots/AGENT_ID/...`
5. Copy the AGENT_ID part

## Connection Setup

When you add Dataverse actions, Power Automate will prompt you to create connections:
- **Dataverse**: Connect to your environment
- **OneDrive for Business**: Connect to your OneDrive account

## Troubleshooting

- **Can't find Copilot components table**: Make sure you're in the correct environment
- **Permission errors**: Ensure your account has access to Dataverse and Copilot Studio
- **Agent ID not working**: Double-check you copied the correct ID from the URL
- **File upload fails**: Verify the OneDrive connection is working