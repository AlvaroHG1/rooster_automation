"""
ROI Online Scraper Module
Downloads monthly roster as .ics file from ROI Online portal.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Download
import yaml

logger = logging.getLogger(__name__)


class ROIScraper:
    """Scraper for ROI Online roster system."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the scraper with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.roi_config = self.config['roi_online']
        self.email = os.getenv('ROI_EMAIL')
        self.password = os.getenv('ROI_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError("ROI_EMAIL and ROI_PASSWORD must be set in environment variables")
    
    def download_roster(self, output_path: str) -> str:
        """
        Download the monthly roster as .ics file.
        
        Args:
            output_path: Directory to save the .ics file
            
        Returns:
            Path to the downloaded .ics file
        """
        logger.info("Starting ROI Online roster download")
        
        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # Navigate to ROI Online
                logger.info("Navigating to ROI Online")
                page.goto(self.roi_config['url'], wait_until='networkidle')
                
                # Login
                logger.info("Logging in")
                self._login(page)
                
                # Wait for roster page to load
                page.wait_for_load_state('networkidle')
                logger.info("Logged in successfully")
                
                # Select month view
                logger.info("Selecting month view")
                self._select_month_view(page)
                
                # Download .ics file
                logger.info("Downloading .ics file")
                ics_path = self._download_ics(page, output_path)
                
                logger.info(f"Successfully downloaded roster to {ics_path}")
                return ics_path
                
            except Exception as e:
                logger.error(f"Error downloading roster: {e}")
                raise
            finally:
                browser.close()
    
    def _login(self, page: Page):
        """Login to ROI Online."""
        # Fill in credentials
        page.fill(f"#{self.roi_config['username_field_id']}", self.email)
        page.fill(f"#{self.roi_config['password_field_id']}", self.password)
        
        # Click login button
        page.click(f"#{self.roi_config['login_button_id']}")
        
        # Wait for navigation
        page.wait_for_load_state('networkidle')
    
    def _select_month_view(self, page: Page):
        """Select the month view radio button."""
        month_radio = f"#{self.roi_config['month_radio_button_id']}"
        page.click(month_radio)
        page.wait_for_load_state('networkidle')
    
    def _download_ics(self, page: Page, output_path: str) -> str:
        """
        Click the calendar export button and download the .ics file.
        
        Args:
            page: Playwright page object
            output_path: Directory to save the file
            
        Returns:
            Path to the downloaded file
        """
        # Create output directory if it doesn't exist
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        # Generate filename with current week number
        week_num = datetime.now().isocalendar()[1]
        year = datetime.now().year
        filename = f"rooster_{year}_week_{week_num:02d}.ics"
        filepath = os.path.join(output_path, filename)
        
        # Set up download handler
        with page.expect_download() as download_info:
            # Click the calendar export button
            page.click(f"#{self.roi_config['calendar_export_button_id']}")
        
        download: Download = download_info.value
        
        # Save the file
        download.save_as(filepath)
        
        return filepath


def main():
    """Test function to run the scraper standalone."""
    import argparse
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Download ROI Online roster')
    parser.add_argument('--output', '-o', default='./downloads',
                        help='Output directory for .ics file')
    args = parser.parse_args()
    
    # Run scraper
    scraper = ROIScraper()
    ics_file = scraper.download_roster(args.output)
    print(f"✓ Roster downloaded to: {ics_file}")


if __name__ == "__main__":
    main()
