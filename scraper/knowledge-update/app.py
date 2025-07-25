#!/usr/bin/env python3
"""
Knowledge Update Service - Flask API
Retrieves TD SYNNEX price files from email attachments and updates Copilot Studio knowledge base
"""

import os
import sys
import json
import logging
import base64
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from email_attachment_client import EmailAttachmentClient
from file_processor import FileProcessor
from sharepoint_uploader import SharePointUploader

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

# Global clients
email_client = None
file_processor = None
sharepoint_uploader = None

def validate_environment():
    """Validate required environment variables"""
    required_vars = [
        'AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET',
        'OUTLOOK_USER_EMAIL', 'CUSTOMER_NUMBER'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        return False
    return True

def initialize_clients():
    """Initialize all service clients"""
    global email_client, file_processor, sharepoint_uploader
    
    if not validate_environment():
        return False
    
    try:
        # Initialize email client
        email_client = EmailAttachmentClient(
            tenant_id=os.getenv('AZURE_TENANT_ID'),
            client_id=os.getenv('AZURE_CLIENT_ID'),
            client_secret=os.getenv('AZURE_CLIENT_SECRET'),
            user_email=os.getenv('OUTLOOK_USER_EMAIL')
        )
        
        # Initialize file processor
        file_processor = FileProcessor(
            customer_number=os.getenv('CUSTOMER_NUMBER', '701601'),
            pattern=os.getenv('SEARCH_PATTERN', r'(\d+)-(\d{2})-(\d{2})-(\d+)\.txt')
        )
        
        # Initialize SharePoint uploader
        sharepoint_uploader = SharePointUploader(
            tenant_id=os.getenv('AZURE_TENANT_ID'),
            client_id=os.getenv('AZURE_CLIENT_ID'),
            client_secret=os.getenv('AZURE_CLIENT_SECRET'),
            site_url=os.getenv('SHAREPOINT_SITE_URL', 'https://hexalinks.sharepoint.com/sites/QuotationsTeam'),
            folder_path=os.getenv('SHAREPOINT_FOLDER_PATH', 'Shared Documents/Quotations-Team-Channel')
        )
        
        logger.info("✅ All clients initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize clients: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for container probes"""
    try:
        if not all([email_client, file_processor, sharepoint_uploader]):
            raise Exception("Clients not initialized")
        
        # Test email connection
        email_client.test_connection()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'message': 'Knowledge update service ready',
            'email_connected': True,
            'clients_initialized': True,
        'sharepoint_connected': sharepoint_uploader.test_connection() if sharepoint_uploader else False
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness probe for container orchestration"""
    return jsonify({
        'status': 'ready',
        'timestamp': datetime.now().isoformat(),
        'clients_ready': all([email_client, file_processor, sharepoint_uploader])
    }), 200

@app.route('/latest-attachment', methods=['GET'])
def get_latest_attachment():
    """
    Get the latest TD SYNNEX price file attachment
    
    Query parameters:
    - max_age_minutes: Maximum age of email to consider (default: 60, ignored if ignore_time_window=true)
    - ignore_time_window: Set to 'true' to ignore time window and get most recent attachment (default: false)
    - download: Set to 'true' to return file content (default: false)
    - upload_sharepoint: Set to 'true' to automatically upload to SharePoint (default: false)
    - delete_previous: Set to 'true' to delete previous TD SYNNEX file after upload (default: true, only when upload_sharepoint=true)
    """
    try:
        if not email_client:
            raise Exception("Email client not initialized")
        
        # Get query parameters
        max_age_minutes = int(request.args.get('max_age_minutes', 60))
        ignore_time_window = request.args.get('ignore_time_window', 'false').lower() == 'true'
        download_content = request.args.get('download', 'false').lower() == 'true'
        upload_sharepoint = request.args.get('upload_sharepoint', 'false').lower() == 'true'
        delete_previous = request.args.get('delete_previous', 'true').lower() == 'true'  # Default to true
        
        if ignore_time_window:
            logger.info(f"🔍 Searching for latest TD SYNNEX attachment (ignoring time window)")
            # Use a very large time window to effectively ignore it
            search_age_minutes = 43200  # 30 days
        else:
            logger.info(f"🔍 Searching for latest TD SYNNEX attachment (max age: {max_age_minutes} minutes)")
            search_age_minutes = max_age_minutes
        
        # Search for emails with attachments
        attachment_info = email_client.get_latest_td_synnex_attachment(
            max_age_minutes=search_age_minutes
        )
        
        if not attachment_info:
            if ignore_time_window:
                message = 'No TD SYNNEX price files found (searched all recent emails)'
            else:
                message = f'No TD SYNNEX price files found in the last {max_age_minutes} minutes'
            
            return jsonify({
                'success': False,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }), 404
        
        response_data = {
            'success': True,
            'attachment_info': attachment_info,
            'timestamp': datetime.now().isoformat()
        }
        
        # Download file content if requested
        if download_content:
            file_content = email_client.download_attachment(
                attachment_info['message_id'],
                attachment_info['attachment_id']
            )
            if file_content:
                response_data['file_content'] = base64.b64encode(file_content).decode()
                response_data['file_size'] = len(file_content)
        
        # Upload to SharePoint if requested
        if upload_sharepoint and download_content:
            file_content = base64.b64decode(response_data['file_content'])
            # Process the file content first
            processed_content = file_processor.process_file(
                attachment_info['filename'],
                file_content
            )
            if processed_content:
                upload_result = sharepoint_uploader.upload_file(
                    filename=attachment_info['filename'],
                    content=processed_content,
                    delete_previous=delete_previous  # Use configurable parameter
                )
                response_data['sharepoint_upload'] = upload_result
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Error retrieving latest attachment: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/attachment-history', methods=['GET'])
def get_attachment_history():
    """
    Get history of TD SYNNEX price file attachments
    
    Query parameters:
    - days: Number of days to look back (default: 7)
    - limit: Maximum number of results (default: 10)
    """
    try:
        if not email_client:
            raise Exception("Email client not initialized")
        
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 10))
        
        logger.info(f"📊 Getting attachment history (last {days} days, limit: {limit})")
        
        history = email_client.get_attachment_history(
            days_back=days,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'history': history,
            'days_searched': days,
            'results_count': len(history),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error retrieving attachment history: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/upload-to-sharepoint', methods=['POST'])
def upload_to_sharepoint():
    """
    Upload latest TD SYNNEX price file to SharePoint
    
    JSON payload:
    {
        "filename": "optional-specific-filename",
        "overwrite": true/false,
        "max_age_minutes": 60,
        "cleanup_old": true/false,
        "delete_previous": true/false  // NEW: Delete previous TD SYNNEX file after upload (default: true)
    }
    """
    try:
        if not all([email_client, sharepoint_uploader]):
            raise Exception("Required clients not initialized")
        
        data = request.get_json() or {}
        filename = data.get('filename')
        overwrite = data.get('overwrite', True)
        cleanup_old = data.get('cleanup_old', False)
        delete_previous = data.get('delete_previous', True)  # NEW: Default to true for automatic cleanup
        max_age_minutes = data.get('max_age_minutes', 60)
        
        logger.info(f"⬆️ Starting SharePoint upload process")
        
        # Get latest attachment if no specific filename provided
        if not filename:
            attachment_info = email_client.get_latest_td_synnex_attachment(
                max_age_minutes=max_age_minutes
            )
            
            if not attachment_info:
                return jsonify({
                    'success': False,
                    'message': f'No TD SYNNEX price files found in the last {max_age_minutes} minutes',
                    'timestamp': datetime.now().isoformat()
                }), 404
            
            filename = attachment_info['filename']
            message_id = attachment_info['message_id']
            attachment_id = attachment_info['attachment_id']
        else:
            # Find specific file by name
            attachment_info = email_client.find_attachment_by_filename(filename)
            if not attachment_info:
                return jsonify({
                    'success': False,
                    'message': f'File {filename} not found in recent emails',
                    'timestamp': datetime.now().isoformat()
                }), 404
            
            message_id = attachment_info['message_id']
            attachment_id = attachment_info['attachment_id']
        
        # Download file content
        logger.info(f"📥 Downloading file: {filename}")
        file_content = email_client.download_attachment(message_id, attachment_id)
        
        if not file_content:
            return jsonify({
                'success': False,
                'message': f'Failed to download file: {filename}',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Process and validate file
        processed_content = file_processor.process_file(filename, file_content)
        if not processed_content:
            return jsonify({
                'success': False,
                'message': f'Failed to process file: {filename}',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Upload to SharePoint with automatic previous file deletion
        logger.info(f"📤 Uploading to SharePoint")
        upload_result = sharepoint_uploader.upload_file(
            filename=filename,
            content=processed_content,
            overwrite=overwrite,
            delete_previous=delete_previous  # Use configurable parameter
        )
        
        # Additional bulk cleanup if requested (for older files beyond just the previous one)
        cleanup_result = None
        if cleanup_old and upload_result.get('success'):
            cleanup_result = sharepoint_uploader.cleanup_old_files(keep_latest=2)  # Keep only current + 1 backup
        
        return jsonify({
            'success': True,
            'filename': filename,
            'file_size': len(file_content),
            'processed_size': len(processed_content),
            'upload_result': upload_result,
            'cleanup_result': cleanup_result,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error uploading to SharePoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/sharepoint-files', methods=['GET'])
def list_sharepoint_files():
    """
    List existing TD SYNNEX files in SharePoint
    
    Query parameters:
    - pattern: File pattern to search for (default: 701601*.txt)
    """
    try:
        if not sharepoint_uploader:
            raise Exception("SharePoint uploader not initialized")
        
        pattern = request.args.get('pattern', '701601*.txt')
        
        logger.info(f"📋 Listing SharePoint files with pattern: {pattern}")
        
        files = sharepoint_uploader.list_existing_files(pattern=pattern)
        
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files),
            'pattern': pattern,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error listing SharePoint files: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/sharepoint-files/<filename>', methods=['DELETE'])
def delete_sharepoint_file(filename):
    """
    Delete a specific file from SharePoint
    """
    try:
        if not sharepoint_uploader:
            raise Exception("SharePoint uploader not initialized")
        
        logger.info(f"🗑️ Deleting SharePoint file: {filename}")
        
        result = sharepoint_uploader.delete_file(filename)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'File {filename} deleted successfully',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'timestamp': datetime.now().isoformat()
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Error deleting SharePoint file: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/sharepoint-cleanup', methods=['POST'])
def cleanup_sharepoint_files():
    """
    Clean up old TD SYNNEX files in SharePoint
    
    JSON payload:
    {
        "keep_latest": 5
    }
    """
    try:
        if not sharepoint_uploader:
            raise Exception("SharePoint uploader not initialized")
        
        data = request.get_json() or {}
        keep_latest = data.get('keep_latest', 5)
        
        logger.info(f"🧹 Cleaning up SharePoint files, keeping latest {keep_latest}")
        
        result = sharepoint_uploader.cleanup_old_files(keep_latest=keep_latest)
        
        return jsonify({
            'success': result['success'],
            'files_deleted': result.get('files_deleted', []),
            'files_kept': result.get('files_kept', []),
            'message': result.get('message', ''),
            'error': result.get('error'),
            'timestamp': datetime.now().isoformat()
        }), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"❌ Error during SharePoint cleanup: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/webhook/power-automate', methods=['POST'])
def power_automate_webhook():
    """
    Webhook endpoint for Power Automate integration
    Receives callbacks and status updates from Power Automate flows
    """
    try:
        data = request.get_json()
        logger.info(f"📨 Received Power Automate webhook: {json.dumps(data, indent=2)}")
        
        # Process webhook data
        webhook_type = data.get('type', 'unknown')
        status = data.get('status', 'unknown')
        message = data.get('message', '')
        
        # Log the webhook event
        logger.info(f"Power Automate {webhook_type}: {status} - {message}")
        
        return jsonify({
            'success': True,
            'message': 'Webhook received successfully',
            'processed_type': webhook_type,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error processing Power Automate webhook: {e}")
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
        'service': 'knowledge-update-service',
        'timestamp': datetime.now().isoformat(),
        'clients_initialized': all([email_client, file_processor, sharepoint_uploader]),
        'endpoints': [
            '/health', '/ready', '/latest-attachment', '/attachment-history',
            '/upload-to-sharepoint', '/sharepoint-files', '/sharepoint-cleanup',
            '/webhook/power-automate', '/status'
        ]
    }), 200

if __name__ == "__main__":
    logger.info("🚀 Starting Knowledge Update Service for TD SYNNEX Price Files")
    
    # Initialize all clients
    if not initialize_clients():
        logger.error("❌ Failed to initialize clients - service will not work properly")
        sys.exit(1)
    
    logger.info("Available endpoints:")
    logger.info("  GET /health - Health check probe")
    logger.info("  GET /ready - Readiness probe")
    logger.info("  GET /latest-attachment - Get latest TD SYNNEX price file")
    logger.info("  GET /attachment-history - Get history of price files")
    logger.info("  POST /upload-to-sharepoint - Upload TD SYNNEX files to SharePoint")
    logger.info("  GET /sharepoint-files - List existing TD SYNNEX files in SharePoint")
    logger.info("  DELETE /sharepoint-files/<filename> - Delete specific file from SharePoint")
    logger.info("  POST /sharepoint-cleanup - Clean up old files in SharePoint")
    logger.info("  POST /webhook/power-automate - Power Automate webhook")
    logger.info("  GET /status - Get service status")
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)