"""
Rooster Automation - Main Orchestration Script
Monitors Gmail for trigger emails and downloads ROI Online roster.
"""

import os
import logging
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
import yaml

from roi_scraper import ROIScraper
from gmail_monitor import GmailMonitor
from file_storage import FileStorage


# Load environment variables
load_dotenv()

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Set up logging
logging.basicConfig(
    level=getattr(logging, config['logging']['level']),
    format=config['logging']['format'],
    handlers=[
        logging.FileHandler(config['logging']['file']),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class RoosterAutomation:
    """Main automation orchestrator."""
    
    def __init__(self):
        """Initialize all components."""
        logger.info("Initializing Rooster Automation")
        
        self.scraper = ROIScraper()
        self.monitor = GmailMonitor()
        self.storage = FileStorage()
        
        self.active_day = config['schedule']['active_day']
        self.start_hour = config['schedule']['start_hour']
        self.end_hour = config['schedule']['end_hour']
        self.check_interval = config['gmail']['check_interval_minutes']
        
        logger.info(f"Active schedule: {self.active_day} {self.start_hour}:00-{self.end_hour}:00")
    
    def is_active_time(self) -> bool:
        """Check if current time is within active schedule."""
        now = datetime.now()
        
        # Check day of week
        day_name = now.strftime('%A').lower()
        if day_name != self.active_day:
            return False
        
        # Check hour
        current_hour = now.hour
        if not (self.start_hour <= current_hour < self.end_hour):
            return False
        
        return True
    
    def download_and_save_roster(self):
        """Download roster and save to shared folder."""
        try:
            logger.info("=" * 60)
            logger.info("Starting roster download process")
            
            # Download roster to temp location
            temp_dir = "./temp_downloads"
            ics_file = self.scraper.download_roster(temp_dir)
            
            # Save to shared folder
            shared_path = self.storage.save_ics_file(ics_file)
            
            logger.info(f"✓ Roster successfully saved to: {shared_path}")
            logger.info("iPhone Shortcuts can now import this file to Apple Calendar")
            
            # Cleanup old files
            self.storage.cleanup_old_files(days_to_keep=90)
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error in download process: {e}", exc_info=True)
    
    def check_email_and_download(self):
        """Check for trigger email and download if found."""
        if not self.is_active_time():
            logger.debug("Outside active time window - skipping check")
            return
        
        logger.info("Checking for trigger email...")
        
        if self.monitor.check_for_trigger_email():
            logger.info("🔔 Trigger email detected! Starting download...")
            self.download_and_save_roster()
        else:
            logger.debug("No trigger email found")
    
    def run(self):
        """Run the automation with scheduled checks."""
        logger.info("=" * 60)
        logger.info("Rooster Automation Started")
        logger.info(f"Active: {self.active_day.capitalize()} {self.start_hour}:00-{self.end_hour}:00")
        logger.info(f"Monitoring: {self.monitor.email_address}")
        logger.info(f"Trigger sender: {self.monitor.trigger_sender}")
        logger.info(f"Check interval: {self.check_interval} minutes")
        logger.info(f"Shared folder: {self.storage.shared_folder}")
        logger.info("=" * 60)
        
        # Schedule the email check
        schedule.every(self.check_interval).minutes.do(self.check_email_and_download)
        
        # Run initial check
        self.check_email_and_download()
        
        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute if scheduled tasks need to run
                
        except KeyboardInterrupt:
            logger.info("Automation stopped by user")


def main():
    """Main entry point."""
    automation = RoosterAutomation()
    automation.run()


if __name__ == "__main__":
    main()
