#!/bin/bash

# TD SYNNEX Knowledge Update Service Startup Script
# Automatically retrieves TD SYNNEX price files from email and updates SharePoint for Copilot Studio

echo "🚀 Starting TD SYNNEX Knowledge Update Service..."

# Check if we're in the correct directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the knowledge-update directory."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Please create .env with required credentials."
    echo "Required variables:"
    echo "  - AZURE_TENANT_ID"
    echo "  - AZURE_CLIENT_ID" 
    echo "  - AZURE_CLIENT_SECRET"
    echo "  - OUTLOOK_USER_EMAIL"
    echo "  - CUSTOMER_NUMBER"
    echo "  - SHAREPOINT_SITE_URL"
    echo "  - SHAREPOINT_FOLDER_PATH"
    echo "Optional notification variables:"
    echo "  - TEAMS_WEBHOOK_URL          # For Teams notifications"
    echo "  - EMAIL_USERNAME             # For email notifications"
    echo "  - EMAIL_PASSWORD             # App password for email"
    exit 1
fi

# Load environment variables
source .env

# Check Python dependencies
echo "📦 Checking Python dependencies..."
python3 -c "import requests, flask, dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing required Python packages..."
    pip3 install requests flask python-dotenv
fi

# Test connections before starting service
echo "🔍 Testing connections..."

# Test email connection
echo "📧 Testing email connection..."
python3 -c "
from email_attachment_client import EmailAttachmentClient
import os
from dotenv import load_dotenv
load_dotenv()

try:
    client = EmailAttachmentClient(
        tenant_id=os.getenv('AZURE_TENANT_ID'),
        client_id=os.getenv('AZURE_CLIENT_ID'), 
        client_secret=os.getenv('AZURE_CLIENT_SECRET'),
        user_email=os.getenv('OUTLOOK_USER_EMAIL')
    )
    client.test_connection()
    print('✅ Email connection successful')
except Exception as e:
    print(f'❌ Email connection failed: {e}')
    exit(1)
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Email connection test failed. Please check your Azure AD credentials."
    exit 1
fi

# Test SharePoint connection (will show permissions error if not granted yet)
echo "📁 Testing SharePoint connection..."
python3 -c "
from sharepoint_uploader import SharePointUploader
import os
from dotenv import load_dotenv
load_dotenv()

try:
    uploader = SharePointUploader(
        tenant_id=os.getenv('AZURE_TENANT_ID'),
        client_id=os.getenv('AZURE_CLIENT_ID'),
        client_secret=os.getenv('AZURE_CLIENT_SECRET'),
        site_url=os.getenv('SHAREPOINT_SITE_URL'),
        folder_path=os.getenv('SHAREPOINT_FOLDER_PATH')
    )
    if uploader.test_connection():
        print('✅ SharePoint connection successful')
    else:
        print('⚠️  SharePoint connection failed - likely missing permissions')
        print('   Service will start but SharePoint uploads will fail until permissions are added')
except Exception as e:
    print(f'⚠️  SharePoint connection failed: {e}')
    print('   Service will start but SharePoint uploads will fail until permissions are added')
" 2>/dev/null

# Test notification service
echo "📢 Testing notification service..."
python3 -c "
from notification_service import NotificationService
import os
from dotenv import load_dotenv
load_dotenv()

try:
    notifier = NotificationService()
    print('✅ Notification service initialized')
    
    # Check configuration
    teams_configured = bool(os.getenv('TEAMS_WEBHOOK_URL'))
    email_configured = bool(os.getenv('EMAIL_USERNAME') and os.getenv('EMAIL_PASSWORD'))
    graph_configured = bool(os.getenv('AZURE_TENANT_ID') and os.getenv('AZURE_CLIENT_ID'))
    
    if teams_configured:
        print('✅ Teams webhook configured')
    else:
        print('⚠️  Teams webhook not configured (TEAMS_WEBHOOK_URL missing)')
    
    if email_configured:
        print('✅ Email credentials configured')
    elif graph_configured:
        print('📧 Email via Graph API configured (SMTP fallback available)')
    else:
        print('⚠️  No email notification method configured')
    
    print('📢 Notifications will be sent on all SharePoint uploads')
    
except Exception as e:
    print(f'⚠️  Notification service failed to initialize: {e}')
    print('   Service will continue but notifications will be disabled')
" 2>/dev/null

echo ""
echo "🌐 Starting Flask service..."
echo "📊 Available endpoints:"
echo "  GET  /health                    - Health check"
echo "  GET  /latest-attachment         - Get latest TD SYNNEX file"
echo "  GET  /attachment-history        - Get attachment history"
echo "  POST /upload-to-sharepoint      - Upload file to SharePoint"
echo "  GET  /sharepoint-files          - List SharePoint files"
echo "  POST /sharepoint-cleanup        - Clean up old files"
echo "  POST /test-notifications        - Test notification system"
echo "  GET  /status                    - Service status"
echo ""
echo "🔗 Service will be available at: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the service"
echo ""

# Start the Flask application
python3 app.py