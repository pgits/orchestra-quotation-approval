#!/usr/bin/env python3
"""
Create proper Power Automate package for import
Generates the correct ZIP format with metadata
"""

import json
import zipfile
import os
import uuid
from datetime import datetime

def create_flow_package():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    # Read the flow definition
    flow_path = os.path.join(base_dir, 'flows', 'copilot-knowledge-refresh-flow.json')
    with open(flow_path, 'r') as f:
        flow_definition = json.load(f)
    
    # Generate unique IDs
    package_id = str(uuid.uuid4())
    flow_id = str(uuid.uuid4())
    
    # Create package manifest
    manifest = {
        "packageSchemaVersion": "1.0",
        "creator": "Copilot Knowledge Refresh Service",
        "description": "Automated knowledge base file refresh for Copilot Studio",
        "createdTime": datetime.utcnow().isoformat() + "Z",
        "packageTelemetryId": package_id,
        "resources": {
            flow_id: {
                "id": flow_id,
                "name": "Copilot-Knowledge-Refresh-Flow",
                "type": "Microsoft.Flow/flows",
                "creationType": "New",
                "details": {
                    "displayName": "Copilot Knowledge Refresh Flow"
                },
                "configurableBy": "User",
                "hierarchy": "Root",
                "dependsOn": []
            }
        }
    }
    
    # Create flow resource file
    flow_resource = {
        "name": "Copilot-Knowledge-Refresh-Flow",
        "id": flow_id,
        "type": "Microsoft.Flow/flows",
        "properties": {
            "apiId": "/providers/Microsoft.PowerApps/apis/shared_logicflows",
            "displayName": "Copilot Knowledge Refresh Flow",
            "iconUri": "https://connectoricons-prod.azureedge.net/releases/v1.0.1664/1.0.1664.3434/logicflows/icon.png",
            "purpose": "NotSpecified",
            "connectionReferences": {
                "shared_commondataservice": {
                    "runtimeSource": "embedded",
                    "connection": {
                        "connectionReferenceLogicalName": "msdyn_copilotcomponents"
                    },
                    "api": {
                        "name": "shared_commondataservice"
                    }
                },
                "shared_onedriveforbusiness": {
                    "runtimeSource": "embedded",
                    "connection": {},
                    "api": {
                        "name": "shared_onedriveforbusiness"
                    }
                }
            },
            "definition": flow_definition["definition"],
            "state": "Started",
            "connectionReferences": {
                "shared_commondataservice": {
                    "connectionName": "shared_commondataservice",
                    "source": "Embedded",
                    "id": "/providers/Microsoft.PowerApps/apis/shared_commondataservice"
                },
                "shared_onedriveforbusiness": {
                    "connectionName": "shared_onedriveforbusiness", 
                    "source": "Embedded",
                    "id": "/providers/Microsoft.PowerApps/apis/shared_onedriveforbusiness"
                }
            }
        }
    }
    
    # Create the package ZIP file
    package_path = os.path.join(base_dir, 'flows', 'CopilotKnowledgeRefreshFlow.zip')
    
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add manifest in Microsoft.Flow folder (required structure)
        zipf.writestr('Microsoft.Flow/manifest.json', json.dumps(manifest, indent=2))
        
        # Add flow definition in Microsoft.Flow/flows folder
        zipf.writestr(f'Microsoft.Flow/flows/{flow_id}.json', json.dumps(flow_resource, indent=2))
    
    print(f"✅ Power Automate package created: {package_path}")
    print(f"📦 Package ID: {package_id}")
    print(f"🔄 Flow ID: {flow_id}")
    print()
    print("You can now import this ZIP file in Power Automate:")
    print("1. Go to https://powerautomate.microsoft.com")
    print("2. Click 'My flows' → 'Import' → 'Import Package (Legacy)'")
    print(f"3. Upload: {package_path}")
    
    return package_path

if __name__ == "__main__":
    create_flow_package()