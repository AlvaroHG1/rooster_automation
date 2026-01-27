"""
Rooster Automation - Main Orchestration Script
Monitors Gmail for trigger emails and downloads ROI Online roster.
"""

import logging
import schedule
import time
from datetime import datetime

from settings import settings
from utils import setup_logging
from roi_scraper import ROIScraper
from gmail_monitor import GmailMonitor
from file_storage import CalendarService

# Initialize logging
setup_logging(
    settings.logging_level,
    settings.logging_format,
    settings.logging_file
)

logger = logging.getLogger(__name__)


class RoosterAutomation:
    """Main automation orchestrator."""
    
    def __init__(self):
        """Initialize all components."""
        logger.info("Initializing Rooster Automation")
        
        self.scraper = ROIScraper()
        self.monitor = GmailMonitor()
        self.storage = CalendarService()
        
        self.logger_info()

    def logger_info(self):
        """Log initialization info."""
        logger.info("=" * 60)
        logger.info(f"Active: {settings.active_day.capitalize()} {settings.start_hour}:00-{settings.end_hour}:00")
        logger.info(f"Monitoring: {settings.gmail_address}")
        logger.info(f"Trigger sender: {settings.trigger_sender}")
        logger.info(f"Check interval: {settings.gmail_check_interval / 60:.0f} minutes")
        logger.info(f"Storage: CalDAV ({settings.caldav_url})")
        logger.info(f"Calendar: {settings.caldav_calendar_name}")
        logger.info("=" * 60)
    
    def is_active_time(self) -> bool:
        """Check if current time is within active schedule."""
        now = datetime.now()
        
        # Check day of week
        day_name = now.strftime('%A').lower()
        if day_name != settings.active_day:
            return False
        
        # Check hour
        current_hour = now.hour
        if not (settings.start_hour <= current_hour < settings.end_hour):
            return False
        
        return True
    
    def download_and_save_roster(self):
        """Download roster and save to CalDAV."""
        try:
            logger.info("=" * 60)
            logger.info("Starting roster download process")
            
            # Download roster to temp location
            temp_dir = "./temp_downloads"
            ics_file = self.scraper.download_roster(temp_dir)
            
            # Save to CalDAV
            result = self.storage.save_ics_file(ics_file)
            logger.info(f"✓ {result}")
            logger.info("Events are now synced to your iCloud Calendar")
            
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
        logger.info("Rooster Automation Started")
        
        # Schedule the email check
        # settings.gmail_check_interval is in seconds
        interval_minutes = int(settings.gmail_check_interval / 60)
        schedule.every(interval_minutes).minutes.do(self.check_email_and_download)
        
        # Run initial check
        logger.info("Running initial email check...")
        try:
            self.check_email_and_download()
        except Exception as e:
            logger.error(f"Initial email check failed: {e}")
        
        logger.info("Entering main monitoring loop...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Automation stopped by user")
            self.storage.close()


def main():
    """Main entry point."""
    automation = RoosterAutomation()
    automation.run()


if __name__ == "__main__":
    main()
