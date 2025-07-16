#!/usr/bin/env python3
"""
Azure Container Main Application
Monitors SharePoint for ec-synnex files and uploads to Copilot Studio
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from sharepoint_monitor import SharePointMonitor
from copilot_uploader import CopilotUploader
from health_server import HealthServer
from azure.identity import ManagedIdentityCredential, ClientSecretCredential
from applicationinsights import TelemetryClient

# Configure logging - force to stdout for Azure Container Apps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Also add immediate print statements for debugging
print("=== APPLICATION STARTING ===", flush=True)
print("Logging configured successfully", flush=True)

logger = logging.getLogger(__name__)

# Immediate startup logging
logger.info("==========================================")
logger.info("COPILOT KNOWLEDGE REFRESH SERVICE STARTING")
logger.info("==========================================")

class CopilotKnowledgeRefreshService:
    def __init__(self):
        """Initialize the service with environment configuration"""
        self.config = self.load_config()
        
        # Initialize Azure credential - use ClientSecretCredential if available, otherwise ManagedIdentity
        client_id = self.config.get('AZURE_CLIENT_ID')
        client_secret = self.config.get('AZURE_CLIENT_SECRET')
        tenant_id = self.config.get('AZURE_TENANT_ID')
        
        logger.info(f"Authentication debug - Client ID: {client_id[:8]}... (length: {len(client_id) if client_id else 0})")
        logger.info(f"Authentication debug - Client Secret: {'[SET]' if client_secret else '[NOT SET]'} (length: {len(client_secret) if client_secret else 0})")
        logger.info(f"Authentication debug - Tenant ID: {tenant_id[:8]}... (length: {len(tenant_id) if tenant_id else 0})")
        
        if client_id and client_secret and tenant_id:
            logger.info("Using ClientSecretCredential for authentication")
            self.credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            logger.info("Using ManagedIdentityCredential for authentication")
            self.credential = ManagedIdentityCredential()
        
        # Initialize Application Insights if configured
        self.telemetry_client = None
        if self.config.get('APPINSIGHTS_INSTRUMENTATION_KEY'):
            self.telemetry_client = TelemetryClient(
                self.config['APPINSIGHTS_INSTRUMENTATION_KEY']
            )
        
        # Initialize components
        self.sharepoint_monitor = SharePointMonitor(
            self.config, 
            self.credential,
            self.telemetry_client
        )
        
        self.copilot_uploader = CopilotUploader(
            self.config,
            self.credential,
            self.telemetry_client
        )
        
        self.health_server = HealthServer(self)
        
        # Service state
        self.is_running = False
        self.last_check_time = None
        self.processed_files = set()
        self.error_count = 0
        
    def load_config(self) -> dict:
        """Load configuration from environment variables"""
        config = {
            # Copilot Studio Configuration
            'AGENT_ID': os.getenv('AGENT_ID', 'e71b63c6-9653-f011-877a-000d3a593ad6'),
            'ENVIRONMENT_ID': os.getenv('ENVIRONMENT_ID', 'Default-33a7afba-68df-4fb5-84ba-abd928569b69'),
            
            # SharePoint Configuration
            'SHAREPOINT_SITE_URL': os.getenv('SHAREPOINT_SITE_URL', 'https://hexalinks.sharepoint.com/sites/QuotationsTeam'),
            'SHAREPOINT_LIBRARY_NAME': os.getenv('SHAREPOINT_LIBRARY_NAME', 'Shared Documents'),
            'SHAREPOINT_FOLDER_PATH': os.getenv('SHAREPOINT_FOLDER_PATH', ''),
            'SHAREPOINT_TENANT': os.getenv('SHAREPOINT_TENANT', 'hexalinks'),
            
            # File Processing Configuration
            'FILE_PATTERN': os.getenv('FILE_PATTERN', 'ec-synnex-'),
            'SUPPORTED_EXTENSIONS': os.getenv('SUPPORTED_EXTENSIONS', '.xls,.xlsx').split(','),
            'MAX_FILE_SIZE': int(os.getenv('MAX_FILE_SIZE', '536870912')),  # 512MB
            
            # Monitoring Configuration
            'CHECK_INTERVAL': int(os.getenv('CHECK_INTERVAL', '30')),  # 30 seconds
            'RETRY_ATTEMPTS': int(os.getenv('RETRY_ATTEMPTS', '3')),
            'RETRY_DELAY': int(os.getenv('RETRY_DELAY', '60')),  # 1 minute
            
            # Azure Configuration
            'AZURE_SUBSCRIPTION_ID': os.getenv('AZURE_SUBSCRIPTION_ID', ''),
            'AZURE_RESOURCE_GROUP': os.getenv('AZURE_RESOURCE_GROUP', ''),
            'APPINSIGHTS_INSTRUMENTATION_KEY': os.getenv('APPINSIGHTS_INSTRUMENTATION_KEY', ''),
            
            # Azure Authentication
            'AZURE_CLIENT_ID': os.getenv('AZURE_CLIENT_ID', ''),
            'AZURE_CLIENT_SECRET': os.getenv('AZURE_CLIENT_SECRET', ''),
            'AZURE_TENANT_ID': os.getenv('AZURE_TENANT_ID', ''),
            
            # Logging Configuration
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'ENABLE_AUDIT_TRAIL': os.getenv('ENABLE_AUDIT_TRAIL', 'true').lower() == 'true'
        }
        
        # Validate required configuration
        required_fields = [
            'AGENT_ID', 'SHAREPOINT_SITE_URL', 'SHAREPOINT_TENANT'
        ]
        
        missing_fields = [field for field in required_fields if not config.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
        
        logger.info(f"Configuration loaded successfully")
        logger.info(f"Agent ID: {config['AGENT_ID']}")
        logger.info(f"SharePoint Site: {config['SHAREPOINT_SITE_URL']}")
        logger.info(f"Check Interval: {config['CHECK_INTERVAL']} seconds")
        
        return config
    
    def start(self):
        """Start the monitoring service"""
        logger.info("Starting Copilot Knowledge Refresh Service")
        logger.info("Current configuration loaded:")
        logger.info(f"  - SharePoint Site: {self.config.get('SHAREPOINT_SITE_URL')}")
        logger.info(f"  - Library: {self.config.get('SHAREPOINT_LIBRARY_NAME')}")
        logger.info(f"  - Folder Path: '{self.config.get('SHAREPOINT_FOLDER_PATH')}'")
        logger.info(f"  - File Pattern: {self.config.get('FILE_PATTERN')}")
        logger.info(f"  - Check Interval: {self.config.get('CHECK_INTERVAL')} seconds")
        
        if self.telemetry_client:
            self.telemetry_client.track_event('ServiceStarted', {
                'agent_id': self.config['AGENT_ID'],
                'sharepoint_site': self.config['SHAREPOINT_SITE_URL']
            })
        
        self.is_running = True
        
        # Start health server in background thread
        health_thread = threading.Thread(target=self.health_server.start, daemon=True)
        health_thread.start()
        
        # Start main monitoring loop
        self.monitor_loop()
    
    def stop(self):
        """Stop the monitoring service"""
        logger.info("Stopping Copilot Knowledge Refresh Service")
        self.is_running = False
        
        if self.telemetry_client:
            self.telemetry_client.track_event('ServiceStopped')
    
    def monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                self.last_check_time = datetime.utcnow()
                logger.info(f"Starting file check at {self.last_check_time}")
                
                # Check for new files
                new_files = self.sharepoint_monitor.check_for_new_files()
                
                if new_files:
                    logger.info(f"Found {len(new_files)} new files to process")
                    self.process_files(new_files)
                else:
                    logger.info("No new files found")
                
                # Reset error count on successful check
                self.error_count = 0
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                
                if self.telemetry_client:
                    self.telemetry_client.track_exception()
                
                # Stop service if too many consecutive errors
                if self.error_count >= 5:
                    logger.error("Too many consecutive errors, stopping service")
                    self.stop()
                    break
            
            # Wait for next check
            if self.is_running:
                logger.info(f"Waiting {self.config['CHECK_INTERVAL']} seconds until next check")
                time.sleep(self.config['CHECK_INTERVAL'])
    
    def process_files(self, files):
        """Process a list of files"""
        for file_info in files:
            try:
                logger.info(f"Processing file: {file_info['name']}")
                
                # Download file from SharePoint
                file_content = self.sharepoint_monitor.download_file(file_info)
                
                if file_content:
                    # Upload to Copilot Studio
                    success = self.copilot_uploader.upload_file(
                        file_info['name'], 
                        file_content
                    )
                    
                    if success:
                        logger.info(f"Successfully processed file: {file_info['name']}")
                        self.processed_files.add(file_info['id'])
                        
                        # Move file to processed folder in SharePoint
                        self.sharepoint_monitor.move_to_processed(file_info)
                        
                        if self.telemetry_client:
                            self.telemetry_client.track_event('FileProcessedSuccessfully', {
                                'filename': file_info['name'],
                                'file_size': str(file_info.get('size', 0))
                            })
                    else:
                        logger.error(f"Failed to upload file to Copilot Studio: {file_info['name']}")
                        
                        if self.telemetry_client:
                            self.telemetry_client.track_event('FileUploadFailed', {
                                'filename': file_info['name']
                            })
                else:
                    logger.error(f"Failed to download file from SharePoint: {file_info['name']}")
                    
            except Exception as e:
                logger.error(f"Error processing file {file_info['name']}: {e}", exc_info=True)
                
                if self.telemetry_client:
                    self.telemetry_client.track_exception()
    
    def get_health_status(self) -> dict:
        """Get current health status for health checks"""
        now = datetime.utcnow()
        
        # Check if last check was recent
        last_check_ok = (
            self.last_check_time is not None and 
            (now - self.last_check_time) < timedelta(minutes=10)
        )
        
        # Check error rate
        error_rate_ok = self.error_count < 3
        
        # Overall health
        healthy = self.is_running and last_check_ok and error_rate_ok
        
        return {
            'status': 'healthy' if healthy else 'unhealthy',
            'timestamp': now.isoformat(),
            'is_running': self.is_running,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'error_count': self.error_count,
            'processed_files_count': len(self.processed_files),
            'config': {
                'agent_id': self.config['AGENT_ID'],
                'sharepoint_site': self.config['SHAREPOINT_SITE_URL'],
                'check_interval': self.config['CHECK_INTERVAL']
            }
        }

def main():
    """Main entry point"""
    try:
        print("=== MAIN FUNCTION STARTING ===", flush=True)
        logger.info("MAIN FUNCTION STARTING - Initializing service...")
        # Initialize and start service
        service = CopilotKnowledgeRefreshService()
        print("=== SERVICE INITIALIZED ===", flush=True)
        logger.info("Service initialized, starting monitoring...")
        service.start()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        if 'service' in locals():
            service.stop()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()