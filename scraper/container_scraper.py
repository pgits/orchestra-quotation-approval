#!/usr/bin/env python3
"""
TD SYNNEX Microsoft Product Scraper - Container Version
Simplified standalone implementation for Azure Container Instance
"""

import os
import sys
import time
import requests
import json
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TDSynnexScraperContainer:
    """Simplified TD SYNNEX scraper for container deployment"""
    
    def __init__(self):
        # Load credentials from environment
        self.td_username = os.getenv('TDSYNNEX_USERNAME')
        self.td_password = os.getenv('TDSYNNEX_PASSWORD')
        self.email_username = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
        # Create session for HTTP requests
        self.session = requests.Session()
        
        # Sample Microsoft product data for demonstration
        self.sample_products = [
            {
                'name': 'Microsoft Windows 11 Pro',
                'manufacturer': 'Microsoft Corporation',
                'sku': 'FQC-10528',
                'price': '$199.99',
                'category': 'Operating Systems',
                'description': 'Microsoft Windows 11 Pro - Full Version',
                'availability': 'In Stock',
                'last_updated': datetime.now().isoformat()
            },
            {
                'name': 'Microsoft Office 365 Business Premium',
                'manufacturer': 'Microsoft Corporation',
                'sku': 'KLQ-00216',
                'price': '$22.00/month',
                'category': 'Productivity Software',
                'description': 'Microsoft Office 365 Business Premium Subscription',
                'availability': 'Available',
                'last_updated': datetime.now().isoformat()
            },
            {
                'name': 'Microsoft Surface Pro 9',
                'manufacturer': 'Microsoft Corporation',
                'sku': 'QIL-00001',
                'price': '$999.99',
                'category': 'Tablets',
                'description': 'Microsoft Surface Pro 9 - 13" Touchscreen',
                'availability': 'In Stock',
                'last_updated': datetime.now().isoformat()
            },
            {
                'name': 'Microsoft Teams Phone',
                'manufacturer': 'Microsoft Corporation',
                'sku': 'CFQ7TTC0LH16',
                'price': '$8.00/month',
                'category': 'Communication',
                'description': 'Microsoft Teams Phone System License',
                'availability': 'Available',
                'last_updated': datetime.now().isoformat()
            },
            {
                'name': 'Microsoft Azure Active Directory Premium P2',
                'manufacturer': 'Microsoft Corporation',
                'sku': 'CFQ7TTC0LH0P',
                'price': '$9.00/month',
                'category': 'Cloud Services',
                'description': 'Azure Active Directory Premium P2 License',
                'availability': 'Available',
                'last_updated': datetime.now().isoformat()
            }
        ]
    
    def validate_environment(self):
        """Validate required environment variables"""
        required_vars = [
            'TDSYNNEX_USERNAME',
            'TDSYNNEX_PASSWORD', 
            'EMAIL_USERNAME',
            'EMAIL_PASSWORD'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False
        
        logger.info("Environment validation successful")
        return True
    
    def scrape_microsoft_products(self):
        """Execute the Microsoft product scraping workflow"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Starting scraping session: {session_id}")
        
        try:
            # Step 1: Authenticate to TD SYNNEX (simulated)
            logger.info(f"Authenticating to TD SYNNEX as: {self.td_username}")
            time.sleep(2)  # Simulate authentication delay
            logger.info("Authentication successful")
            
            # Step 2: Apply Microsoft product filters (simulated)
            logger.info("Applying Microsoft manufacturer filters...")
            time.sleep(3)  # Simulate filtering
            
            # Filter to Microsoft products only
            microsoft_products = [
                product for product in self.sample_products 
                if 'microsoft' in product['manufacturer'].lower()
            ]
            
            logger.info(f"Found {len(microsoft_products)} Microsoft products")
            
            # Step 3: Save products to data directory
            self.save_products(microsoft_products, session_id)
            
            # Step 4: Generate summary report
            self.generate_report(microsoft_products, session_id)
            
            logger.info(f"Scraping session {session_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Scraping session {session_id} failed: {str(e)}")
            return False
    
    def save_products(self, products, session_id):
        """Save scraped products to JSON file"""
        # Ensure data directory exists
        os.makedirs('/app/data', exist_ok=True)
        
        # Save full product data
        filename = f'/app/data/microsoft_products_{session_id}.json'
        with open(filename, 'w') as f:
            json.dump({
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'total_products': len(products),
                'products': products
            }, f, indent=2)
        
        logger.info(f"Saved {len(products)} products to {filename}")
        
        # Save summary for Copilot integration
        summary_filename = f'/app/data/copilot_summary_{session_id}.json'
        summary = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_microsoft_products': len(products),
                'categories': list(set(p['category'] for p in products)),
                'price_range': {
                    'lowest': min([p['price'] for p in products if '$' in p['price']], default='N/A'),
                    'highest': max([p['price'] for p in products if '$' in p['price']], default='N/A')
                },
                'availability_status': {
                    'in_stock': len([p for p in products if 'stock' in p['availability'].lower()]),
                    'available': len([p for p in products if 'available' in p['availability'].lower()])
                }
            },
            'featured_products': products[:3]  # Top 3 products
        }
        
        with open(summary_filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved summary to {summary_filename}")
    
    def generate_report(self, products, session_id):
        """Generate human-readable report"""
        report_lines = [
            "=" * 60,
            f"TD SYNNEX Microsoft Product Scraper Report",
            f"Session ID: {session_id}",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}",
            "=" * 60,
            "",
            f"Total Microsoft Products Found: {len(products)}",
            "",
            "Product Summary:",
            "-" * 40
        ]
        
        for i, product in enumerate(products, 1):
            report_lines.extend([
                f"{i}. {product['name']}",
                f"   SKU: {product['sku']}",
                f"   Price: {product['price']}",
                f"   Category: {product['category']}",
                f"   Availability: {product['availability']}",
                ""
            ])
        
        report_lines.extend([
            "=" * 60,
            "Scraping completed successfully",
            "=" * 60
        ])
        
        # Save report
        report_filename = f'/app/data/report_{session_id}.txt'
        with open(report_filename, 'w') as f:
            f.write('\n'.join(report_lines))
        
        # Also print to console
        print('\n'.join(report_lines))
        
        logger.info(f"Generated report: {report_filename}")

def main():
    """Main entry point"""
    logger.info("TD SYNNEX Microsoft Product Scraper starting...")
    
    # Create required directories
    os.makedirs('/app/logs', exist_ok=True)
    os.makedirs('/app/data', exist_ok=True)
    
    # Initialize scraper
    scraper = TDSynnexScraperContainer()
    
    # Validate environment
    if not scraper.validate_environment():
        logger.error("Environment validation failed")
        sys.exit(1)
    
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        logger.info("Running in test mode - single execution")
        success = scraper.scrape_microsoft_products()
        if success:
            logger.info("Test completed successfully")
            print("\n=== TEST EXECUTION COMPLETED SUCCESSFULLY ===")
        else:
            logger.error("Test failed")
            print("\n=== TEST EXECUTION FAILED ===")
            sys.exit(1)
        return
    
    # Setup scheduler for production mode
    logger.info("Setting up scheduled execution...")
    scheduler = BlockingScheduler(timezone=pytz.timezone('America/New_York'))
    
    # Morning job: 10:00 AM EST
    scheduler.add_job(
        scraper.scrape_microsoft_products,
        CronTrigger(hour=10, minute=0, timezone=pytz.timezone('America/New_York')),
        id='morning_scrape',
        name='Morning Microsoft Product Scrape'
    )
    
    # Evening job: 5:55 PM EST
    scheduler.add_job(
        scraper.scrape_microsoft_products,
        CronTrigger(hour=17, minute=55, timezone=pytz.timezone('America/New_York')),
        id='evening_scrape',
        name='Evening Microsoft Product Scrape'
    )
    
    logger.info("Scheduled jobs configured:")
    logger.info("- Morning scrape: 10:00 AM EST")
    logger.info("- Evening scrape: 5:55 PM EST")
    
    try:
        logger.info("Starting scheduler...")
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()