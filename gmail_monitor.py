"""
Gmail Monitor Module
Monitors Gmail inbox for trigger emails.
"""

import imaplib
import email
import logging
import time
from email.header import decode_header
from typing import Optional, Callable, Dict, Any

from settings import settings
from utils import retry_on_failure

logger = logging.getLogger(__name__)


class GmailMonitor:
    """Monitor Gmail inbox for trigger emails."""
    
    def __init__(self):
        """Initialize Gmail monitor."""
        self.last_checked_uid: Optional[bytes] = None
        logger.info(f"GmailMonitor initialized for {settings.gmail_address}")
    
    @retry_on_failure(retries=3, delay=5)
    def connect(self, timeout: int = 10) -> imaplib.IMAP4_SSL:
        """Connect to Gmail via IMAP."""
        logger.debug("Connecting to Gmail IMAP...")
        
        mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=timeout)
        mail.login(settings.gmail_address, settings.gmail_app_password)
        
        logger.debug("✓ Successfully connected to Gmail")
        return mail
    
    def check_for_trigger_email(self) -> bool:
        """Check if there's a new email from the trigger sender."""
        mail = None
        try:
            mail = self.connect(timeout=15)
            mail.select("inbox")
            
            sender = settings.trigger_sender
            search_criteria = f'(OR FROM "{sender}" SUBJECT "Fwd: Nieuw rooster gepubliceerd")'
            
            logger.debug(f"Searching for emails: {search_criteria}")
            status, messages = mail.search(None, search_criteria)
            
            if status != "OK":
                logger.error("Failed to search emails")
                return False
            
            email_ids = messages[0].split()
            if not email_ids:
                logger.debug("No emails found from trigger sender")
                return False
            
            latest_uid = email_ids[-1]
            
            if self.last_checked_uid is None:
                logger.info(f"First run - storing latest UID: {latest_uid.decode()}")
                self.last_checked_uid = latest_uid
                return False
            
            if latest_uid > self.last_checked_uid:
                self._log_email_details(mail, latest_uid)
                self.last_checked_uid = latest_uid
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking emails: {e}")
            return False
        finally:
            if mail:
                try:
                    mail.logout()
                except:
                    pass

    def _log_email_details(self, mail, uid):
        """Log details of the found email."""
        try:
            status, msg_data = mail.fetch(uid, "(RFC822)")
            if status == "OK":
                email_body = msg_data[0][1]
                msg = email.message_from_bytes(email_body)
                subject = self._decode_header(msg["Subject"])
                logger.info(f"New trigger email! Subject: {subject}")
        except Exception as e:
            logger.warning(f"Could not fetch email details: {e}")

    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        if not header:
            return ""
        decoded = decode_header(header)
        result = ""
        for part, encoding in decoded:
            if isinstance(part, bytes):
                result += part.decode(encoding or 'utf-8')
            else:
                result += part
        return result
    
    def monitor(self, callback: Callable, check_interval: Optional[int] = None):
        """Monitor inbox and call callback when trigger email is found."""
        interval = check_interval or settings.gmail_check_interval
        logger.info(f"Starting monitoring loop (checking every {interval}s)")
        
        while True:
            try:
                if self.check_for_trigger_email():
                    logger.info("Trigger detected! Executing callback...")
                    callback()
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(interval)

if __name__ == "__main__":
    from utils import setup_logging
    setup_logging("INFO", "%(asctime)s - %(message)s", "test_monitor.log")
    
    monitor = GmailMonitor()
    monitor.monitor(lambda: print("Callback executed!"), check_interval=10)
