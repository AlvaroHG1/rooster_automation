"""
ROI Online Scraper Module
Downloads monthly roster as .ics file from ROI Online portal.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
import re
import time
from playwright.sync_api import sync_playwright, Page, Download

from app.core.settings import settings

logger = logging.getLogger(__name__)


class ROIScraper:
    """Scraper for ROI Online roster system."""
    
    def __init__(self):
        """Initialize scraper."""
        logger.info("ROIScraper initialized")
    
    def download_roster(self, output_path: str, target_week: int = None, target_year: int = None) -> str:
        """
        Download the monthly roster as .ics file.
        
        Args:
            output_path: Directory to save the .ics file
            target_week: Optional specific week number to download
            target_year: Optional specific year (defaults to current year)
        """
        logger.info(f"Starting ROI Online roster download (Week: {target_week or 'Current'})")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                self._navigate_and_login(page)
                
                if target_week:
                    self._navigate_to_week(page, target_week, target_year)
                
                self._select_month_view(page)
                ics_path = self._download_ics(page, output_path, target_week, target_year)
                
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
    
    def _navigate_to_week(self, page: Page, target_week: int, target_year: int = None):
        """Navigate to the specific week."""
        target_year = target_year or datetime.now().year
        logger.info(f"Navigating to week {target_week}, {target_year}")
        
        # Get current displayed week
        # Format is usually "2025 week 05"
        week_display = page.inner_text(f"#{settings.roi_week_display}")
        logger.debug(f"Current week display: {week_display}")
        
        match = re.search(r'(\d{4})\s+week\s+(\d+)', week_display, re.IGNORECASE)
        if not match:
            logger.warning(f"Could not parse week display: {week_display}. Skipping navigation.")
            return

        current_year = int(match.group(1))
        current_week = int(match.group(2))
        
        # Simple logic: assume we are close to the target.
        # If difference is huge, maybe we should skip (safety break)
        diff = (target_year - current_year) * 52 + (target_week - current_week)
        
        if diff == 0:
            logger.info("Already at target week.")
            return
            
        if abs(diff) > 20:
             logger.warning(f"Target week is too far ({diff} weeks). Safety break.")
             return
             
        button_id = settings.roi_next_week_button if diff > 0 else settings.roi_prev_week_button
        clicks = abs(diff)
        
        logger.info(f"Clicking {clicks} times to reach target...")
        
        for i in range(clicks):
            page.click(f"#{button_id}")
            # Wait for update - relying on networkidle might be enough, but adding small sleep for safety if AJAX is fast but update slow
            page.wait_for_load_state('networkidle')
            time.sleep(0.5) 
            
        # Verify
        new_display = page.inner_text(f"#{settings.roi_week_display}")
        logger.info(f"Navigation complete. New display: {new_display}")

    def _download_ics(self, page: Page, output_path: str, target_week: int = None, target_year: int = None) -> str:
        """Handle the file download."""
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        week_num = target_week or datetime.now().isocalendar()[1]
        year = target_year or datetime.now().year
        
        filename = f"rooster_{year}_week_{week_num:02d}.ics"
        filepath = os.path.join(output_path, filename)
        
        logger.info("Initiating download...")
        with page.expect_download() as download_info:
            page.click(f"#{settings.roi_calendar_export_button}")
        
        download: Download = download_info.value
        download.save_as(filepath)
        
        return filepath


if __name__ == "__main__":
    from app.core.utils import setup_logging
    setup_logging("INFO", "%(asctime)s - %(message)s", "test_scraper.log")
    
    # Simple standalone run
    scraper = ROIScraper()
    try:
        path = scraper.download_roster("./downloads")
        print(f"Downloaded to: {path}")
    except Exception as e:
        print(f"Failed: {e}")
