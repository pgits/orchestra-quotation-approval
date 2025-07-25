#!/usr/bin/env python3
"""
Diagnose upload errors by examining table schemas and field requirements.
"""

import os
import json
import logging
from dotenv import load_dotenv
import requests
from msal import ConfidentialClientApplication

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UploadDiagnostics:
    def __init__(self):
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.dataverse_url = os.getenv('DATAVERSE_URL')
        
        self.access_token = None
        self._authenticate()

    def _authenticate(self):
        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        
        scope = [f"{self.dataverse_url}/.default"]
        result = app.acquire_token_for_client(scopes=scope)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            logger.info("Authentication successful")
        else:
            raise Exception(f"Auth failed: {result.get('error_description')}")

    def get_table_schema(self, table_name):
        """Get the schema/metadata for a specific table."""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'OData-MaxVersion': '4.0'
        }
        
        try:
            # Get entity definition
            url = f"{self.dataverse_url}/api/data/v9.2/EntityDefinitions(LogicalName='{table_name}')"
            params = {
                '$select': 'LogicalName,DisplayName,PrimaryIdAttribute,PrimaryNameAttribute',
                '$expand': 'Attributes($select=LogicalName,DisplayName,RequiredLevel,AttributeType,IsPrimaryId,IsPrimaryName)'
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get schema for {table_name}: {e}")
            return None

    def analyze_existing_records(self, table_name, limit=3):
        """Analyze existing records to understand the required structure."""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'OData-MaxVersion': '4.0'
        }
        
        try:
            url = f"{self.dataverse_url}/api/data/v9.2/{table_name}"
            params = {
                '$top': limit,
                '$orderby': 'createdon desc'
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json().get('value', [])
            
        except Exception as e:
            logger.error(f"Failed to get records from {table_name}: {e}")
            return []

    def test_minimal_create(self, table_name, data):
        """Test creating a record with minimal data to see what's required."""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'OData-MaxVersion': '4.0'
        }
        
        try:
            url = f"{self.dataverse_url}/api/data/v9.2/{table_name}"
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                return {'success': True, 'data': response.json()}
            else:
                return {
                    'success': False, 
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

def main():
    diagnostics = UploadDiagnostics()
    
    print("=" * 80)
    print("UPLOAD DIAGNOSTICS REPORT")
    print("=" * 80)
    
    # 1. Analyze knowledgearticles table
    print("\n1. KNOWLEDGE ARTICLES TABLE ANALYSIS")
    print("-" * 45)
    
    ka_schema = diagnostics.get_table_schema('knowledgearticle')
    if ka_schema:
        print(f"Primary ID: {ka_schema.get('PrimaryIdAttribute')}")
        print(f"Primary Name: {ka_schema.get('PrimaryNameAttribute')}")
        
        # Show required fields
        required_fields = []
        optional_fields = []
        
        for attr in ka_schema.get('Attributes', []):
            field_name = attr.get('LogicalName')
            required_level_obj = attr.get('RequiredLevel', {})
            required_level = required_level_obj.get('Value', 'None') if isinstance(required_level_obj, dict) else str(required_level_obj)
            
            attr_type_obj = attr.get('AttributeType', {})
            attr_type = attr_type_obj.get('Value', 'Unknown') if isinstance(attr_type_obj, dict) else str(attr_type_obj)
            
            if required_level in ['SystemRequired', 'ApplicationRequired']:
                required_fields.append((field_name, attr_type, required_level))
            else:
                optional_fields.append((field_name, attr_type, required_level))
        
        print(f"\nRequired fields ({len(required_fields)}):")
        for field, type_val, req_level in required_fields[:10]:
            print(f"  - {field}: {type_val} ({req_level})")
        
        print(f"\nOptional fields (first 10 of {len(optional_fields)}):")
        for field, type_val, req_level in optional_fields[:10]:
            print(f"  - {field}: {type_val} ({req_level})")
    
    # Analyze existing knowledge articles
    ka_records = diagnostics.analyze_existing_records('knowledgearticles', 2)
    if ka_records:
        print(f"\nExisting knowledge articles sample:")
        for i, record in enumerate(ka_records):
            print(f"  Record {i+1} fields: {list(record.keys())[:10]}")
    else:
        print("\nNo existing knowledge articles found.")
    
    # Test minimal knowledge article creation
    print(f"\n2. TESTING MINIMAL KNOWLEDGE ARTICLE CREATION")
    print("-" * 55)
    
    minimal_ka_data = {
        'title': 'Test Knowledge Article',
    }
    
    result = diagnostics.test_minimal_create('knowledgearticles', minimal_ka_data)
    print(f"Minimal create test: {'SUCCESS' if result['success'] else 'FAILED'}")
    if not result['success']:
        print(f"Error: {result.get('error', 'Unknown error')[:500]}")
    
    # 3. Analyze botcomponents table
    print(f"\n3. BOT COMPONENTS TABLE ANALYSIS")
    print("-" * 40)
    
    bc_schema = diagnostics.get_table_schema('botcomponent')
    if bc_schema:
        print(f"Primary ID: {bc_schema.get('PrimaryIdAttribute')}")
        print(f"Primary Name: {bc_schema.get('PrimaryNameAttribute')}")
        
        # Show required fields for botcomponents
        required_fields = []
        for attr in bc_schema.get('Attributes', []):
            field_name = attr.get('LogicalName')
            required_level_obj = attr.get('RequiredLevel', {})
            required_level = required_level_obj.get('Value', 'None') if isinstance(required_level_obj, dict) else str(required_level_obj)
            
            attr_type_obj = attr.get('AttributeType', {})
            attr_type = attr_type_obj.get('Value', 'Unknown') if isinstance(attr_type_obj, dict) else str(attr_type_obj)
            
            if required_level in ['SystemRequired', 'ApplicationRequired']:
                required_fields.append((field_name, attr_type, required_level))
        
        print(f"\nRequired fields ({len(required_fields)}):")
        for field, type_val, req_level in required_fields:
            print(f"  - {field}: {type_val} ({req_level})")
    
    # Analyze existing bot components structure
    bc_records = diagnostics.analyze_existing_records('botcomponents', 3)
    if bc_records:
        print(f"\nExisting bot components sample:")
        for i, record in enumerate(bc_records):
            comp_type = record.get('componenttype')
            name = record.get('name', 'Unnamed')
            has_content = bool(record.get('content'))
            print(f"  Type {comp_type}: {name} (Content: {has_content})")
            print(f"    Fields: {list(record.keys())[:15]}")
    
    # Test minimal bot component creation
    print(f"\n4. TESTING MINIMAL BOT COMPONENT CREATION")
    print("-" * 50)
    
    minimal_bc_data = {
        'name': 'Test Component',
        'componenttype': 10
    }
    
    result = diagnostics.test_minimal_create('botcomponents', minimal_bc_data)
    print(f"Minimal create test: {'SUCCESS' if result['success'] else 'FAILED'}")
    if not result['success']:
        print(f"Error: {result.get('error', 'Unknown error')[:500]}")
    
    # 5. Recommendations
    print(f"\n5. UPLOAD STRATEGY RECOMMENDATIONS")
    print("-" * 40)
    
    print("Based on diagnostics:")
    print("1. Check required field validation errors")
    print("2. Use exact field names from existing records")
    print("3. Consider permissions - may need different authentication scope")
    print("4. Test with Power Platform CLI for comparison")
    print("5. Review Copilot Studio documentation for knowledge upload APIs")

if __name__ == "__main__":
    main()