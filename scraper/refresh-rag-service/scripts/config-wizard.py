#!/usr/bin/env python3
"""
Configuration Wizard for Copilot Studio Knowledge Refresh
Interactive setup without CLI dependencies
"""

import json
import os
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config', 'config.json')
    
    print("=== Copilot Studio Configuration Wizard ===")
    print()
    
    # Load existing config
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {config_path}")
        sys.exit(1)
    
    print("We'll help you configure the system step by step.")
    print("Press Enter to keep existing values, or type new values.")
    print()
    
    # Agent ID
    current_agent_id = config['copilotStudio']['agentId']
    print(f"Current Agent ID: {current_agent_id}")
    agent_id = input("Enter your Copilot Studio Agent ID: ").strip()
    if agent_id:
        config['copilotStudio']['agentId'] = agent_id
    
    # Environment ID
    current_env_id = config['copilotStudio']['environment']['id']
    print(f"Current Environment ID: {current_env_id}")
    env_id = input("Enter your Environment ID (optional): ").strip()
    if env_id:
        config['copilotStudio']['environment']['id'] = env_id
    
    # Trigger URL
    current_trigger_url = config['powerAutomate']['triggerUrl']
    print(f"Current Trigger URL: {current_trigger_url}")
    print("This is the HTTP POST URL from your Power Automate flow.")
    trigger_url = input("Enter your Power Automate trigger URL: ").strip()
    if trigger_url:
        config['powerAutomate']['triggerUrl'] = trigger_url
    
    # File path
    current_file_path = config['fileSettings']['localFilePath']
    print(f"Current file path: {current_file_path}")
    file_path = input("Enter your file path (or press Enter for default): ").strip()
    if file_path:
        config['fileSettings']['localFilePath'] = file_path
    
    # Save configuration
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\n✅ Configuration saved successfully!")
        print(f"Config file: {config_path}")
        
        # Test configuration
        print("\n=== Configuration Test ===")
        if config['copilotStudio']['agentId'] != "YOUR_AGENT_ID_HERE":
            print("✅ Agent ID configured")
        else:
            print("❌ Agent ID not configured")
            
        if config['powerAutomate']['triggerUrl'] != "YOUR_FLOW_TRIGGER_URL_HERE":
            print("✅ Trigger URL configured")
        else:
            print("❌ Trigger URL not configured")
            
        print("\nYou can now test the upload with:")
        print("python3 scripts/upload-to-copilot.py ~/Downloads/ec-synnex-701601-0708-0927.xls")
        
    except Exception as e:
        print(f"ERROR: Failed to save configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
