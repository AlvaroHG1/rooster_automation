"""
ROI Online Scraper Module
Downloads monthly roster as .ics file from ROI Online portal.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Download

from settings import settings

logger = logging.getLogger(__name__)


class ROIScraper:
    """Scraper for ROI Online roster system."""
    
    def __init__(self):
        """Initialize scraper."""
        logger.info("ROIScraper initialized")
    
    def download_roster(self, output_path: str) -> str:
        """Download the monthly roster as .ics file."""
        logger.info("Starting ROI Online roster download")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                self._navigate_and_login(page)
                self._select_month_view(page)
                ics_path = self._download_ics(page, output_path)
                
                logger.info(f"Successfully downloaded roster to {ics_path}")
                return ics_path
                
            except Exception as e:
                logger.error(f"Error downloading roster: {e}")
                raise
            finally:
                browser.close()
    
    def _navigate_and_login(self, page: Page):
        """Navigate to URL and login."""
        logger.info(f"Navigating to {settings.roi_url}")
        page.goto(settings.roi_url, wait_until='networkidle')
        
        logger.info("Logging in...")
        page.fill(f"#{settings.roi_username_field}", settings.roi_email)
        page.fill(f"#{settings.roi_password_field}", settings.roi_password)
        
        page.click(f"#{settings.roi_login_button}")
        page.wait_for_load_state('networkidle')
        logger.info("Logged in successfully")
    
    def _select_month_view(self, page: Page):
        """Select the month view."""
        logger.debug("Selecting month view")
        page.click(f"#{settings.roi_month_radio}")
        page.wait_for_load_state('networkidle')
    
    def _download_ics(self, page: Page, output_path: str) -> str:
        """Handle the file download."""
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        week_num = datetime.now().isocalendar()[1]
        year = datetime.now().year
        filename = f"rooster_{year}_week_{week_num:02d}.ics"
        filepath = os.path.join(output_path, filename)
        
        logger.info("Initiating download...")
        with page.expect_download() as download_info:
            page.click(f"#{settings.roi_calendar_export_button}")
        
        download: Download = download_info.value
        download.save_as(filepath)
        
        return filepath


if __name__ == "__main__":
    from utils import setup_logging
    setup_logging("INFO", "%(asctime)s - %(message)s", "test_scraper.log")
    
    # Simple standalone run
    scraper = ROIScraper()
    try:
        path = scraper.download_roster("./downloads")
        print(f"Downloaded to: {path}")
    except Exception as e:
        print(f"Failed: {e}")
