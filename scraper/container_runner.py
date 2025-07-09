#!/usr/bin/env python3
"""
Container runner for TD SYNNEX scraper in Azure Container Instances
Optimized for headless operation and container environment
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from local_production_scraper import LocalProductionScraper

# Configure logging for container environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/output/container_scraper.log')
    ]
)
logger = logging.getLogger(__name__)

class ContainerScraper:
    """Container-optimized TD SYNNEX scraper"""
    
    def __init__(self):
        self.output_dir = Path("/app/output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Verify environment
        self.verify_environment()
        
        # Initialize scraper
        self.scraper = LocalProductionScraper()
        
    def verify_environment(self):
        """Verify container environment is ready"""
        logger.info("🔍 Verifying container environment...")
        
        # Check Chrome installation
        chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/google-chrome-stable')
        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')
        
        if not os.path.exists(chrome_bin):
            logger.error(f"❌ Chrome binary not found: {chrome_bin}")
            sys.exit(1)
            
        if not os.path.exists(chromedriver_path):
            logger.error(f"❌ ChromeDriver not found: {chromedriver_path}")
            sys.exit(1)
        
        # Check credentials
        td_username = os.environ.get('TDSYNNEX_USERNAME')
        td_password = os.environ.get('TDSYNNEX_PASSWORD')
        
        if not td_username or not td_password:
            logger.error("❌ Missing TD SYNNEX credentials")
            logger.error("Set TDSYNNEX_USERNAME and TDSYNNEX_PASSWORD environment variables")
            sys.exit(1)
        
        logger.info("✅ Container environment verified")
        logger.info(f"Chrome: {chrome_bin}")
        logger.info(f"ChromeDriver: {chromedriver_path}")
        logger.info(f"Username: {td_username[:3]}***")
        
    def run_scraping(self):
        """Execute scraping in container environment"""
        logger.info("🚀 Starting TD SYNNEX scraping in container...")
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_time = time.time()
        
        try:
            # Run the scraping
            success, result = self.scraper.run_production_scraping()
            
            duration = time.time() - start_time
            
            # Create result summary
            summary = {
                'session_id': session_id,
                'success': success,
                'duration_seconds': duration,
                'timestamp': datetime.now().isoformat(),
                'result': result,
                'container_info': {
                    'chrome_version': self.get_chrome_version(),
                    'chromedriver_version': self.get_chromedriver_version(),
                    'python_version': sys.version,
                    'environment': 'Azure Container Instance'
                }
            }
            
            # Save summary
            summary_file = self.output_dir / f"scraping_summary_{session_id}.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            if success:
                logger.info("✅ Scraping completed successfully!")
                logger.info(f"📊 Duration: {duration:.2f} seconds")
                logger.info(f"📁 Results saved to: {summary_file}")
                return True
            else:
                logger.error("❌ Scraping failed!")
                logger.error(f"Error: {result}")
                return False
                
        except Exception as e:
            logger.error(f"💥 Container scraping failed: {str(e)}")
            
            # Save error info
            error_info = {
                'session_id': session_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': time.time() - start_time
            }
            
            error_file = self.output_dir / f"scraping_error_{session_id}.json"
            with open(error_file, 'w') as f:
                json.dump(error_info, f, indent=2)
            
            return False
    
    def get_chrome_version(self):
        """Get Chrome version"""
        try:
            import subprocess
            result = subprocess.run(['/usr/bin/google-chrome-stable', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.stdout.strip() if result.returncode == 0 else "Unknown"
        except:
            return "Unknown"
    
    def get_chromedriver_version(self):
        """Get ChromeDriver version"""
        try:
            import subprocess
            result = subprocess.run(['/usr/local/bin/chromedriver', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.stdout.strip() if result.returncode == 0 else "Unknown"
        except:
            return "Unknown"
    
    def run_health_check(self):
        """Run basic health check"""
        logger.info("🏥 Running health check...")
        
        try:
            # Check Chrome
            chrome_version = self.get_chrome_version()
            logger.info(f"Chrome: {chrome_version}")
            
            # Check ChromeDriver
            chromedriver_version = self.get_chromedriver_version()
            logger.info(f"ChromeDriver: {chromedriver_version}")
            
            # Check credentials
            if os.environ.get('TDSYNNEX_USERNAME') and os.environ.get('TDSYNNEX_PASSWORD'):
                logger.info("✅ Credentials configured")
            else:
                logger.error("❌ Missing credentials")
                return False
            
            logger.info("✅ Health check passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False

def main():
    """Main container entry point"""
    logger.info("🐳 Starting TD SYNNEX Container Scraper")
    logger.info("=" * 60)
    
    # Check for health check mode
    if len(sys.argv) > 1 and sys.argv[1] == 'health':
        scraper = ContainerScraper()
        success = scraper.run_health_check()
        sys.exit(0 if success else 1)
    
    # Normal scraping mode
    try:
        scraper = ContainerScraper()
        success = scraper.run_scraping()
        
        if success:
            logger.info("🎉 Container scraping completed successfully!")
        else:
            logger.error("💥 Container scraping failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()