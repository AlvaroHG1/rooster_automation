
# Script to verify the navigation logic without needing trigger emails
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.roi_scraper import ROIScraper
from datetime import datetime
import logging

def verify_navigation():
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    scraper = ROIScraper()
    
    # Calculate NEXT week
    current_week = datetime.now().isocalendar()[1]
    target_week = current_week + 1
    
    print(f"--- Verifying navigation to NEXT week: {target_week} ---")
    
    try:
        # We will try to download next week's roster
        path = scraper.download_roster("./temp_downloads", target_week=target_week)
        print(f"SUCCESS: Downloaded roster to {path}")
        print("Please manually inspect the downloaded ICS file content or name to confirm it matches the target week.")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    verify_navigation()
