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
        """Navigate to the specific week using robust ISO date math."""
        target_year = target_year or datetime.now().year
        logger.info(f"Navigating to week {target_week}, {target_year}")
        
        MAX_RETRIES = 5  # preventing infinite loops if navigation fails repeatedly
        MAX_CLICKS = 30  # preventing infinite loops if target is unreachable
        
        for attempt in range(MAX_RETRIES):
             # Get current displayed week
            try:
                week_display = page.inner_text(f"#{settings.roi_week_display}", timeout=5000)
            except Exception as e:
                logger.warning(f"Could not read week display: {e}. Retrying...")
                continue

            logger.debug(f"Current week display: {week_display}")
            
            match = re.search(r'(\d{4})\s+week\s+(\d+)', week_display, re.IGNORECASE)
            if not match:
                logger.warning(f"Could not parse week display: {week_display}. Stopping navigation.")
                return

            current_year = int(match.group(1))
            current_week = int(match.group(2))
            
            # Use ISO date math to calculate exact week difference
            try:
                # %G = ISO Year, %V = ISO Week, %u = Weekday (1=Mon)
                current_date = datetime.strptime(f"{current_year} {current_week} 1", "%G %V %u")
                target_date = datetime.strptime(f"{target_year} {target_week} 1", "%G %V %u")
                
                diff_days = (target_date - current_date).days
                diff_weeks = int(diff_days / 7)
            except ValueError as e:
                logger.error(f"Date calculation error: {e}")
                return

            if diff_weeks == 0:
                logger.info("✓ Successfully reached target week.")
                return

            if abs(diff_weeks) > MAX_CLICKS:
                 logger.warning(f"Target is too far ({diff_weeks} weeks). Safety break.")
                 return
                 
            # Click towards the target
            button_id = settings.roi_next_week_button if diff_weeks > 0 else settings.roi_prev_week_button
            
            # Optimize clicking: Don't click all at once if gap is huge, but do small batches
            # Here we click once and check again to be safe and robust against network lag
            # Or we could click a few times. Let's click min(abs(diff), 5) times to speed up but re-check often.
            clicks_to_perform = min(abs(diff_weeks), 5)
            
            logger.info(f"Gap is {diff_weeks} weeks. Clicking {clicks_to_perform} times...")
            
            for _ in range(clicks_to_perform):
                page.click(f"#{button_id}")
                # Small wait between clicks to ensure UI registers them
                time.sleep(0.2)
            
            # Wait for meaningful update
            page.wait_for_load_state('networkidle')
            time.sleep(0.5)
            
        logger.warning("Max retries reached without hitting target week.")

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
