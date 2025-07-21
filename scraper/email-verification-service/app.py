#!/usr/bin/env python3
"""
Email Verification Service - Flask API
Reads verification codes from Outlook emails for TD SYNNEX scraper
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from outlook_client import OutlookClient

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global outlook client
outlook_client = None

def initialize_outlook_client():
    """Initialize the Outlook client with credentials"""
    global outlook_client
    
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID') 
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    user_email = os.getenv('OUTLOOK_USER_EMAIL', 'pgits@hexalinks.com')
    
    if not all([tenant_id, client_id, client_secret]):
        logger.error("Missing required Azure credentials")
        return False
    
    try:
        outlook_client = OutlookClient(tenant_id, client_id, client_secret, user_email)
        logger.info("✅ Outlook client initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Outlook client: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if outlook_client is None:
            raise Exception("Outlook client not initialized")
        
        # Test connection to Graph API
        outlook_client.test_connection()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'message': 'Email verification service ready',
            'outlook_connected': True
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/verification-code', methods=['GET'])
def get_verification_code():
    """
    Get the latest verification code from TD SYNNEX emails
    
    Query parameters:
    - max_age_minutes: Maximum age of email to consider (default: 10)
    - sender: Email sender to filter by (default: do_not_reply@tdsynnex.com)
    """
    try:
        if outlook_client is None:
            raise Exception("Outlook client not initialized")
        
        # Get query parameters
        max_age_minutes = int(request.args.get('max_age_minutes', 10))
        sender = request.args.get('sender', 'do_not_reply@tdsynnex.com')
        
        logger.info(f"🔍 Searching for verification code from {sender} (max age: {max_age_minutes} minutes)")
        
        # Get verification code from email
        verification_code = outlook_client.get_latest_verification_code(
            sender=sender,
            max_age_minutes=max_age_minutes
        )
        
        if verification_code:
            logger.info(f"✅ Found verification code: {verification_code}")
            return jsonify({
                'success': True,
                'verification_code': verification_code,
                'timestamp': datetime.now().isoformat(),
                'sender': sender
            }), 200
        else:
            logger.warning(f"⚠️ No verification code found from {sender}")
            return jsonify({
                'success': False,
                'message': f'No verification code found from {sender} in the last {max_age_minutes} minutes',
                'timestamp': datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Error getting verification code: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/test-email', methods=['GET'])
def test_email_connection():
    """Test endpoint to verify email connection and recent emails"""
    try:
        if outlook_client is None:
            raise Exception("Outlook client not initialized")
        
        # Get recent emails for testing
        recent_emails = outlook_client.get_recent_emails(count=5)
        
        return jsonify({
            'success': True,
            'message': 'Email connection test successful',
            'recent_emails': [
                {
                    'subject': email.get('subject', 'No subject'),
                    'sender': email.get('sender', 'Unknown sender'),
                    'received_time': email.get('received_time', 'Unknown time')
                }
                for email in recent_emails
            ],
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error testing email connection: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get service status"""
    return jsonify({
        'status': 'running',
        'service': 'email-verification-service',
        'timestamp': datetime.now().isoformat(),
        'outlook_initialized': outlook_client is not None,
        'endpoints': ['/health', '/verification-code', '/test-email', '/status']
    }), 200

if __name__ == "__main__":
    logger.info("🌐 Starting Email Verification Service for TD SYNNEX Scraper")
    
    # Initialize Outlook client
    if not initialize_outlook_client():
        logger.error("❌ Failed to initialize Outlook client - service will not work properly")
        sys.exit(1)
    
    logger.info("Available endpoints:")
    logger.info("  GET /health - Health check")
    logger.info("  GET /verification-code - Get latest verification code")
    logger.info("  GET /test-email - Test email connection")
    logger.info("  GET /status - Get service status")
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)