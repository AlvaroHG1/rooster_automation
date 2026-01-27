"""
Verification script for the refactoring.
Checks if settings load correctly and components can be instantiated.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from app.core.settings import settings
from app.core.utils import setup_logging
from app.services.roi_scraper import ROIScraper
from app.services.gmail_monitor import GmailMonitor
from app.services.calendar_service import CalendarService

def verify():
    print("1. Verifying Settings...")
    try:
        print(f"   - ROI URL: {settings.roi_url}")
        print(f"   - Gmail Interval: {settings.gmail_check_interval}")
        print(f"   - CalDAV URL: {settings.caldav_url}")
    except Exception as e:
        print(f"   FAIL: {e}")
        return False
        
    print("\n2. Verifying Components Initialization...")
    try:
        print("   - Initializing ROIScraper...")
        scraper = ROIScraper()
        
        print("   - Initializing GmailMonitor...")
        monitor = GmailMonitor()
        
        print("   - Initializing CalendarService...")
        storage = CalendarService()
        
    except Exception as e:
        print(f"   FAIL: {e}")
        return False
        
    print("\n3. Verifying Logging...")
    try:
        setup_logging("DEBUG", "%(message)s", "verify_test.log")
        logging.getLogger("test").info("   - Logging works")
    except Exception as e:
        print(f"   FAIL: {e}")
        return False
        
    print("\nSUCCESS: All components initialized correctly.")
    return True

if __name__ == "__main__":
    if verify():
        sys.exit(0)
    else:
        sys.exit(1)
