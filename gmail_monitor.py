"""
Gmail Monitor Module
Monitors Gmail inbox for trigger emails from noreply@staff.nl
"""

import os
import logging
from datetime import datetime
from typing import Optional, Callable
import imaplib
import email
from email.header import decode_header
import time

logger = logging.getLogger(__name__)


class GmailMonitor:
    """Monitor Gmail inbox for trigger emails."""
    
    def __init__(self):
        """Initialize Gmail monitor with credentials from environment."""
        self.email_address = os.getenv('GMAIL_ADDRESS')
        self.app_password = os.getenv('GMAIL_APP_PASSWORD')
        self.trigger_sender = os.getenv('TRIGGER_EMAIL_SENDER', 'noreply@staff.nl')
        
        if not self.email_address or not self.app_password:
            raise ValueError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set")
        
        self.last_checked_uid = None
    
    def connect(self) -> imaplib.IMAP4_SSL:
        """Connect to Gmail via IMAP."""
        logger.info("Connecting to Gmail")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(self.email_address, self.app_password)
        return mail
    
    def check_for_trigger_email(self) -> bool:
        """
        Check if there's a new email from the trigger sender.
        
        Returns:
            True if trigger email found, False otherwise
        """
        try:
            mail = self.connect()
            mail.select("inbox")
            
            # Search for emails from trigger sender
            search_criteria = f'(FROM "{self.trigger_sender}")'
            logger.debug(f"Searching for emails with criteria: {search_criteria}")
            
            status, messages = mail.search(None, search_criteria)
            
            if status != "OK":
                logger.error("Failed to search emails")
                mail.logout()
                return False
            
            email_ids = messages[0].split()
            
            if not email_ids:
                logger.debug("No emails found from trigger sender")
                mail.logout()
                return False
            
            # Get the latest email UID
            latest_uid = email_ids[-1]
            
            # Check if this is a new email (we haven't seen it before)
            if self.last_checked_uid is None:
                # First run - just store the UID, don't trigger
                logger.info(f"First run - storing latest UID: {latest_uid}")
                self.last_checked_uid = latest_uid
                mail.logout()
                return False
            
            if latest_uid > self.last_checked_uid:
                # New email found!
                logger.info(f"New trigger email found! UID: {latest_uid}")
                
                # Fetch email details for logging
                status, msg_data = mail.fetch(latest_uid, "(RFC822)")
                if status == "OK":
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    subject = self._decode_header(email_message["Subject"])
                    from_addr = email_message.get("From")
                    date = email_message.get("Date")
                    
                    logger.info(f"Email details - From: {from_addr}, Subject: {subject}, Date: {date}")
                
                self.last_checked_uid = latest_uid
                mail.logout()
                return True
            
            logger.debug("No new emails since last check")
            mail.logout()
            return False
            
        except Exception as e:
            logger.error(f"Error checking emails: {e}")
            return False
    
    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        if header is None:
            return ""
        decoded = decode_header(header)
        result = ""
        for part, encoding in decoded:
            if isinstance(part, bytes):
                result += part.decode(encoding or 'utf-8')
            else:
                result += part
        return result
    
    def monitor(self, callback: Callable, check_interval: int = 600):
        """
        Monitor inbox and call callback when trigger email is found.
        
        Args:
            callback: Function to call when trigger email is found
            check_interval: Seconds between checks (default: 600 = 10 minutes)
        """
        logger.info(f"Starting email monitoring (checking every {check_interval}s)")
        
        while True:
            try:
                if self.check_for_trigger_email():
                    logger.info("Trigger email detected! Calling callback...")
                    callback()
                else:
                    logger.debug("No trigger email found")
                
                # Wait before next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(check_interval)


def main():
    """Test function to run the monitor standalone."""
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    def test_callback():
        print("✓ Trigger email detected!")
    
    monitor = GmailMonitor()
    print(f"Monitoring {monitor.email_address} for emails from {monitor.trigger_sender}")
    print("Press Ctrl+C to stop")
    
    monitor.monitor(test_callback, check_interval=30)  # Check every 30 seconds for testing


if __name__ == "__main__":
    main()
