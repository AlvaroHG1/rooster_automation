"""
Rooster Automation - Main Orchestration Script
Monitors Gmail for trigger emails and downloads ROI Online roster.
"""

import logging
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

from app.services.roi_scraper import ROIScraper
from app.services.gmail_monitor import GmailMonitor
from app.services.calendar_service import CalendarService
from app.core.settings import settings
from app.core.logging_config import setup_logging


# Load environment variables
load_dotenv()

# Set up logging centrally
setup_logging(
    level_name=settings.logging.level,
    format_str=settings.logging.format,
    file_path=settings.logging.file
)

logger = logging.getLogger(__name__)


class RoosterAutomation:
    """Main automation orchestrator."""
    
    def __init__(self):
        """Initialize all components."""
        logger.info("Initializing Rooster Automation")
        
        self.scraper = ROIScraper()
        self.monitor = GmailMonitor()
        
        # Initialize CalDAV storage
        logger.info("Using CalDAV storage (iCloud Calendar)")
        self.storage = CalendarService()
        
        self.active_days = settings.schedule.active_days
        self.start_hour = settings.schedule.start_hour
        self.end_hour = settings.schedule.end_hour
        
    def is_active_time(self) -> bool:
        """Check if current time is within active schedule."""
        now = datetime.now()
        
        # Check day of week
        day_name = now.strftime('%A').lower()
        if day_name not in self.active_days:
            return False
        
        # Check hour
        current_hour = now.hour
        if not (self.start_hour <= current_hour < self.end_hour):
            return False
        
        return True
    
    def download_and_save_roster(self, target_week: int = None):
        """
        Download roster and save to shared folder or CalDAV.
        
        Args:
            target_week: Optional week number to download
        """
        try:
            logger.info("=" * 60)
            logger.info(f"Starting roster download process (Target Week: {target_week or 'Default'})")
            
            # Download roster to temp location
            temp_dir = "./temp_downloads"
            ics_file = self.scraper.download_roster(temp_dir, target_week=target_week)
            
            # Save to CalDAV
            result = self.storage.save_ics_file(ics_file)
            logger.info(f"✓ {result}")
            logger.info("Events are now synced to your iCloud Calendar")
            
            # Auto-cleanup old events (now fast thanks to server-side search)
            self.storage.delete_old_events(days_to_keep=90)
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error in download process: {e}", exc_info=True)
    
    def check_email_and_download(self):
        """Check for trigger email and download if found."""
        if not self.is_active_time():
            logger.debug("Outside active time window - skipping check")
            return
        
        logger.info("Checking for trigger email...")
        
        result = self.monitor.check_for_trigger_email()
        if result["found"]:
            logger.info("🔔 Trigger email detected! Starting download...")
            self.download_and_save_roster(target_week=result.get("week"))
        else:
            logger.debug("No trigger email found")
    
    def run(self):
        """Run the automation with scheduled checks."""
        logger.info("=" * 60)
        logger.info("Rooster Automation Started")
        days_display = ', '.join(d.capitalize() for d in self.active_days)
        logger.info(f"Active days: {days_display} ({self.start_hour}:00-{self.end_hour}:00)")
        logger.info(f"Check interval: {settings.gmail.check_interval_minutes * 60} seconds")
        logger.info(f"Storage: CalDAV ({settings.caldav.url})")
        logger.info(f"Calendar: {settings.caldav.calendar_name}")
        logger.info("=" * 60)
        
        # Schedule the email check
        # settings.gmail_check_interval is in seconds
        interval_minutes = settings.gmail.check_interval_minutes
        schedule.every(interval_minutes).minutes.do(self.check_email_and_download)
        
        # Run initial check (with error handling to prevent startup hang)
        logger.info("Running initial email check...")
        try:
            self.check_email_and_download()
        except Exception as e:
            logger.error(f"Initial email check failed: {e}")
            logger.info("Will retry on next scheduled check")
        
        logger.info("Entering main monitoring loop...")
        
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
