#!/usr/bin/env python3
"""
Azure Container Runner for TD SYNNEX Scraper with Enhanced 2FA Debugging
Incorporates learnings from local proxy runs for production Azure deployment
"""

import os
import sys
import time
import json
import logging
import threading
import signal
from datetime import datetime
from pathlib import Path
from production_scraper_with_2fa import ProductionScraperWith2FA
from verification_listener import VerificationListener, app
from flask import Flask

# Configure logging for Azure Container Instances
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/azure_container.log')
    ]
)
logger = logging.getLogger(__name__)

class AzureContainerRunner:
    """Azure Container Instance runner with enhanced 2FA debugging capabilities"""
    
    def __init__(self):
        self.verification_listener = None
        self.flask_thread = None
        self.scraper = None
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Configure Azure-specific environment
        self.setup_azure_environment()
    
    def setup_azure_environment(self):
        """Configure environment for Azure Container Instances"""
        logger.info("🏗️ Setting up Azure Container Instance environment...")
        
        # Set default environment variables for Azure
        os.environ.setdefault('HEADLESS_MODE', 'true')
        os.environ.setdefault('DEBUG_MODE', 'true')
        os.environ.setdefault('SCREENSHOT_INTERVAL', '10')
        
        # Configure proxy if provided
        proxy_host = os.getenv('PROXY_HOST')
        proxy_port = os.getenv('PROXY_PORT')
        if proxy_host and proxy_port:
            logger.info(f"🔗 Proxy configuration detected: {proxy_host}:{proxy_port}")
        else:
            logger.info("🔗 No proxy configuration found")
        
        # Create necessary directories
        directories = [
            '/app/output',
            '/app/logs',
            '/app/debug_screenshots',
            '/app/debug_info',
            '/app/production_scraper_data/debug_screenshots',
            '/app/production_scraper_data/debug_info',
            '/app/production_scraper_data/downloads'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Created directory: {directory}")
        
        # Log environment configuration
        logger.info("🌐 Environment Configuration:")
        logger.info(f"  HEADLESS_MODE: {os.getenv('HEADLESS_MODE', 'true')}")
        logger.info(f"  DEBUG_MODE: {os.getenv('DEBUG_MODE', 'false')}")
        logger.info(f"  SCREENSHOT_INTERVAL: {os.getenv('SCREENSHOT_INTERVAL', '10')}")
        logger.info(f"  PROXY_HOST: {proxy_host or 'Not configured'}")
        logger.info(f"  PROXY_PORT: {proxy_port or 'Not configured'}")
    
    def start_verification_listener(self):
        """Start the Flask verification listener API in a separate thread"""
        logger.info("🚀 Starting verification listener API...")
        
        def run_flask():
            try:
                app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
            except Exception as e:
                logger.error(f"❌ Flask app error: {e}")
        
        self.flask_thread = threading.Thread(target=run_flask, daemon=True)
        self.flask_thread.start()
        
        # Wait for Flask to start
        time.sleep(2)
        logger.info("✅ Verification listener API started on port 5001")
    
    def run_scraper_with_retry(self, max_retries=3):
        """Run the scraper with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🚀 Starting scraper (attempt {attempt + 1}/{max_retries})...")
                
                # Create scraper instance
                self.scraper = ProductionScraperWith2FA()
                
                # Run the scraper
                success = self.scraper.run_scraper()
                
                if success:
                    logger.info("✅ Scraper completed successfully!")
                    return True
                else:
                    logger.error(f"❌ Scraper failed on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.error(f"❌ Scraper error on attempt {attempt + 1}: {e}")
                
            # Wait before retry (except on last attempt)
            if attempt < max_retries - 1:
                wait_time = 60 * (attempt + 1)  # Progressive backoff
                logger.info(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        logger.error("❌ All scraper attempts failed")
        return False
    
    def create_session_summary(self):
        """Create a comprehensive session summary"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_file = f"/app/logs/azure_session_summary_{timestamp}.json"
            
            summary = {
                "timestamp": timestamp,
                "container_type": "Azure Container Instance",
                "environment": {
                    "headless_mode": os.getenv('HEADLESS_MODE'),
                    "debug_mode": os.getenv('DEBUG_MODE'),
                    "screenshot_interval": os.getenv('SCREENSHOT_INTERVAL'),
                    "proxy_host": os.getenv('PROXY_HOST'),
                    "proxy_port": os.getenv('PROXY_PORT')
                },
                "directories": {
                    "output": "/app/output",
                    "logs": "/app/logs",
                    "debug_screenshots": "/app/debug_screenshots",
                    "debug_info": "/app/debug_info"
                },
                "api_endpoints": {
                    "verification_listener": "http://localhost:5001/2fa-challenge",
                    "status_check": "http://localhost:5001/2fa-status",
                    "health_check": "http://localhost:8080/health"
                }
            }
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"📋 Session summary saved to: {summary_file}")
            return summary_file
            
        except Exception as e:
            logger.error(f"❌ Error creating session summary: {e}")
            return None
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
        
        # Stop scraper if running
        if self.scraper and hasattr(self.scraper, 'driver') and self.scraper.driver:
            try:
                self.scraper.driver.quit()
                logger.info("🔄 Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
        
        # Create final session summary
        self.create_session_summary()
        
        logger.info("👋 Container shutdown complete")
        sys.exit(0)
    
    def run(self):
        """Main execution method with continuous 2FA waiting mode"""
        logger.info("🚀 Starting Azure Container Runner for TD SYNNEX Scraper")
        logger.info("🔄 Running in CONTINUOUS 2FA WAITING MODE")
        logger.info("=" * 70)
        
        try:
            # Create initial session summary
            self.create_session_summary()
            
            # Start verification listener API
            self.start_verification_listener()
            
            # Check if we should run in continuous mode
            continuous_mode = os.getenv('CONTINUOUS_MODE', 'true').lower() == 'true'
            
            if continuous_mode:
                logger.info("🔄 CONTINUOUS MODE: Container will stay alive waiting for 2FA challenges")
                return self.run_continuous_mode()
            else:
                logger.info("🎯 SINGLE RUN MODE: Running scraper once")
                # Run scraper with retry logic
                success = self.run_scraper_with_retry()
                
                if success:
                    logger.info("🎉 Container execution completed successfully!")
                    return 0
                else:
                    logger.error("💥 Container execution failed!")
                    return 1
                
        except KeyboardInterrupt:
            logger.info("🛑 Container interrupted by user")
            return 1
        except Exception as e:
            logger.error(f"💥 Unexpected container error: {e}")
            return 1
        finally:
            # Final cleanup
            if self.scraper and hasattr(self.scraper, 'driver') and self.scraper.driver:
                try:
                    self.scraper.driver.quit()
                    logger.info("🔄 Browser closed")
                except:
                    pass
            
            # Create final session summary
            self.create_session_summary()
            
            logger.info("⏱️ Container execution finished")
    
    def run_continuous_mode(self):
        """Run container in continuous mode waiting for 2FA challenges"""
        logger.info("🔄 Starting continuous 2FA waiting mode...")
        
        # Import and set up global verification listener access
        from verification_listener import verification_listener
        
        # Pre-emptively start waiting for codes (manual mode)
        verification_listener.start_waiting()
        logger.info("✅ Container is now waiting for 2FA verification codes")
        logger.info("📡 Send codes to: http://td-synnex-scraper-enhanced.eastus.azurecontainer.io:5001/2fa-challenge")
        
        # Keep container alive and responsive
        try:
            while self.running:
                # Check if we received a verification code
                if verification_listener.verification_code:
                    logger.info(f"✅ Received verification code: {verification_listener.verification_code}")
                    
                    # Store the code and trigger scraper run
                    received_code = verification_listener.verification_code
                    verification_listener.verification_code = None
                    
                    logger.info(f"🚀 Starting scraper session with verification code: {received_code}")
                    
                    try:
                        # Create and run scraper instance
                        scraper_success = self.run_scraper_with_retry(max_retries=1)
                        
                        if scraper_success:
                            logger.info(f"✅ Scraper completed successfully with code: {received_code}")
                        else:
                            logger.error(f"❌ Scraper failed with code: {received_code}")
                            
                    except Exception as e:
                        logger.error(f"❌ Exception during scraper run with code {received_code}: {e}")
                    
                    logger.info("🔄 Ready for next verification code...")
                
                # Sleep to avoid busy waiting
                time.sleep(5)
                
                # Log heartbeat every minute
                if int(time.time()) % 60 == 0:
                    logger.info("💓 Container heartbeat - waiting for 2FA challenges...")
                    
        except KeyboardInterrupt:
            logger.info("🛑 Continuous mode interrupted")
            return 0
        
        logger.info("🔚 Continuous mode ended")
        return 0

def main():
    """Main function for Azure Container Instance"""
    runner = AzureContainerRunner()
    return runner.run()

if __name__ == "__main__":
    sys.exit(main())