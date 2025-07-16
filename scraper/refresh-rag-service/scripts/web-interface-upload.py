#!/usr/bin/env python3
"""
Web Interface Upload Solution
Works within organizational security constraints
Uses browser-based authentication instead of programmatic auth
"""

import json
import os
import sys
import base64
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from threading import Thread
import time

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/callback'):
            # Parse the callback URL for auth code
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            if 'code' in query_params:
                self.server.auth_code = query_params['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'''
                <html>
                <body>
                    <h1>Authentication Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
                ''')
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body><h1>Authentication Failed</h1></body></html>')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress log messages

class WebInterfaceUploader:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()
        
    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ERROR: Configuration file not found: {self.config_path}")
            sys.exit(1)
    
    def create_upload_html(self, file_path):
        """Create HTML page for manual upload"""
        filename = os.path.basename(file_path)
        agent_id = self.config['copilotStudio']['agentId']
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        file_size = len(file_content)
        file_ext = os.path.splitext(filename)[1].lower()
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Copilot Studio Knowledge Upload</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            color: #0078d4;
            border-bottom: 2px solid #0078d4;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .file-info {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .step {{
            margin: 20px 0;
            padding: 15px;
            background-color: #e7f3ff;
            border-left: 4px solid #0078d4;
        }}
        .code-block {{
            background-color: #f1f1f1;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            word-break: break-all;
        }}
        .warning {{
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
        .success {{
            background-color: #d4edda;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #28a745;
            margin: 20px 0;
        }}
        button {{
            background-color: #0078d4;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        button:hover {{
            background-color: #106ebe;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">Copilot Studio Knowledge Upload</h1>
        
        <div class="file-info">
            <h3>File Information</h3>
            <p><strong>File:</strong> {filename}</p>
            <p><strong>Size:</strong> {file_size:,} bytes</p>
            <p><strong>Type:</strong> {file_ext}</p>
            <p><strong>Agent ID:</strong> {agent_id}</p>
        </div>
        
        <div class="warning">
            <h3>⚠️ Organizational Security Notice</h3>
            <p>Your organization has security restrictions that prevent direct API access. This page provides manual steps to upload your file through the web interface.</p>
        </div>
        
        <div class="step">
            <h3>Step 1: Access Copilot Studio</h3>
            <p>Click the button below to open Copilot Studio in your browser:</p>
            <button onclick="window.open('https://copilotstudio.microsoft.com/environments/{self.config['copilotStudio']['environment']['id']}/bots/{agent_id}/knowledge', '_blank')">
                Open Copilot Studio
            </button>
        </div>
        
        <div class="step">
            <h3>Step 2: Navigate to Knowledge Base</h3>
            <p>In Copilot Studio:</p>
            <ol>
                <li>Find "Nathan's Hardware Buddy v.1" agent</li>
                <li>Click on the agent to open it</li>
                <li>Go to the "Knowledge" tab</li>
                <li>Look for existing "ec-synnex-" files and delete them</li>
            </ol>
        </div>
        
        <div class="step">
            <h3>Step 3: Upload New File</h3>
            <p>In the Knowledge section:</p>
            <ol>
                <li>Click "Add knowledge" or "+" button</li>
                <li>Select "Files" as the knowledge source</li>
                <li>Upload your file: <code>{filename}</code></li>
                <li>Wait for processing to complete</li>
            </ol>
        </div>
        
        <div class="step">
            <h3>Step 4: Alternative - Use Power Automate</h3>
            <p>If direct upload doesn't work, you can use Power Automate:</p>
            <button onclick="window.open('https://powerautomate.microsoft.com', '_blank')">
                Open Power Automate
            </button>
            <p>Then follow the manual flow creation guide in the documentation.</p>
        </div>
        
        <div class="success">
            <h3>✅ Automation Option</h3>
            <p>Once you have the process working manually, you can automate it by:</p>
            <ol>
                <li>Setting up a OneDrive folder sync</li>
                <li>Creating a Power Automate flow that monitors the folder</li>
                <li>Using SharePoint document library integration</li>
            </ol>
        </div>
        
        <div class="step">
            <h3>File Location</h3>
            <p>Your file is located at:</p>
            <div class="code-block">{file_path}</div>
            <p>You can drag and drop this file directly into the Copilot Studio interface.</p>
        </div>
        
        <div class="step">
            <h3>Need Help?</h3>
            <p>If you encounter issues:</p>
            <ol>
                <li>Check that you have permission to modify the Copilot Studio agent</li>
                <li>Verify you're in the correct environment</li>
                <li>Contact your IT administrator for API access permissions</li>
            </ol>
        </div>
    </div>
    
    <script>
        // Auto-open Copilot Studio after 3 seconds
        setTimeout(function() {{
            if (confirm('Open Copilot Studio automatically?')) {{
                window.open('https://copilotstudio.microsoft.com/environments/{self.config['copilotStudio']['environment']['id']}/bots/{agent_id}/knowledge', '_blank');
            }}
        }}, 3000);
    </script>
</body>
</html>
        """
        
        return html_template
    
    def run(self, file_path=None):
        """Generate web interface for manual upload"""
        if not file_path:
            file_path = os.path.expanduser(self.config['fileSettings']['localFilePath'])
        
        if not os.path.exists(file_path):
            print(f"ERROR: File not found: {file_path}")
            return False
        
        # Create HTML file
        html_content = self.create_upload_html(file_path)
        html_path = os.path.join(os.path.dirname(self.config_path), 'upload_interface.html')
        
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        print(f"🌐 Web interface created: {html_path}")
        print(f"📁 File to upload: {os.path.basename(file_path)}")
        print(f"🆔 Agent ID: {self.config['copilotStudio']['agentId']}")
        print()
        print("Opening web interface in your browser...")
        
        # Open in browser
        webbrowser.open(f'file://{html_path}')
        
        print()
        print("=== MANUAL UPLOAD INSTRUCTIONS ===")
        print("1. The web page will guide you through the upload process")
        print("2. You'll upload the file directly through Copilot Studio's web interface")
        print("3. This bypasses all API restrictions and security issues")
        print()
        print("Your file is ready for upload!")
        
        return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 web-interface-upload.py <file_path>")
        print("Example: python3 web-interface-upload.py ~/Downloads/ec-synnex-701601-0708-0927.xls")
        sys.exit(1)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config', 'config.json')
    
    uploader = WebInterfaceUploader(config_path)
    success = uploader.run(sys.argv[1])
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()