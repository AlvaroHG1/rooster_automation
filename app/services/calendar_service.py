"""
File Storage Module
Handles saving .ics files to CalDAV server (e.g., iCloud Calendar).
"""

import logging
import os
import caldav
import requests
from datetime import datetime, timedelta
from icalendar import Calendar
from typing import List, Optional

from app.core.settings import settings
from app.core.utils import retry_on_failure

logger = logging.getLogger(__name__)


class CalendarService:
    """Manages .ics file upload to CalDAV server."""
    
    def __init__(self):
        """Initialize Calendar Service."""
        self._client: Optional[caldav.DAVClient] = None
        self._principal = None
        self._calendar_cache = None
        
        logger.info("CalendarService initialized")
    
    @property
    def client(self) -> caldav.DAVClient:
        """Get CalDAV client, creating connection if needed."""
        if self._client is None:
            self._connect()
        return self._client
    
    @property
    def principal(self):
        """Get CalDAV principal, creating connection if needed."""
        if self._principal is None:
            self._connect()
        return self._principal
    
    @retry_on_failure(retries=3, delay=2, backoff=2)
    def _connect(self):
        """Establish connection to CalDAV server."""
        logger.info(f"Connecting to CalDAV server: {settings.caldav_url}")
        
        self._client = caldav.DAVClient(
            url=settings.caldav_url,
            username=settings.caldav_username,
            password=settings.caldav_password
        )
        
        # Test connection by getting principal
        self._principal = self._client.principal()
        logger.info("✓ Successfully connected to CalDAV server")

    def _reset_connection(self):
        """Reset connection state."""
        self._client = None
        self._principal = None
        self._calendar_cache = None
        logger.debug("Connection state reset")

    @retry_on_failure(retries=2, delay=1)
    def get_calendar(self):
        """Get or find the calendar for storing roster events."""
        if self._calendar_cache is not None:
            return self._calendar_cache
        
        calendars = self.principal.calendars()
        target_name = settings.caldav_calendar_name
        
        # Try to find existing calendar by name
        for cal in calendars:
            if cal.name == target_name:
                logger.info(f"Found calendar: {target_name}")
                self._calendar_cache = cal
                return cal
        
        # Fallback to first available calendar
        if calendars:
            logger.warning(
                f"Calendar '{target_name}' not found. "
                f"Using first available: {calendars[0].name}"
            )
            self._calendar_cache = calendars[0]
            return calendars[0]
        
        raise ValueError("No calendars found on CalDAV server")
    
    def save_ics_file(self, source_path: str) -> str:
        """
        Upload .ics file content to CalDAV server.
        Parses the .ics file and uploads each event individually.
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        logger.info(f"Reading .ics file: {source_path}")
        with open(source_path, 'rb') as f:
            cal = Calendar.from_ical(f.read())
        
        calendar = self.get_calendar()
        return self._upload_events(calendar, cal)

    def _upload_events(self, calendar, cal: Calendar) -> str:
        """Upload events from parsed calendar to CalDAV."""
        logger.info(f"Uploading events to calendar: {calendar.name}")
        
        events_uploaded = 0
        events_failed = 0
        failed_events = []
        
        for component in cal.walk():
            if component.name == "VEVENT":
                if self._upload_single_event(calendar, cal, component):
                    events_uploaded += 1
                else:
                    events_failed += 1
                    failed_events.append(component.get('SUMMARY', 'Unknown'))

        logger.info(f"Upload complete: {events_uploaded} succeeded, {events_failed} failed")
        
        if events_uploaded == 0:
            raise ValueError("No events were successfully uploaded")
            
        if failed_events:
            logger.warning(f"Failed events: {failed_events[:3]}...")

        return f"Uploaded {events_uploaded} events to calendar: {calendar.name}"

    def _upload_single_event(self, calendar, source_cal, component) -> bool:
        """Helper to upload a single event with retry."""
        event_summary = component.get('SUMMARY', 'No title')
        
        try:
            # Create a new calendar object for the single event
            event_cal = Calendar()
            for key in source_cal.keys():
                if key not in ['VEVENT']:
                    event_cal.add(key, source_cal[key])
            event_cal.add_component(component)
            
            event_ics = event_cal.to_ical().decode('utf-8')
            
            # Simple retry for the save operation
            self._save_event_with_retry(calendar, event_ics)
            
            logger.debug(f"  ✓ Uploaded: {event_summary}")
            return True
            
        except Exception as e:
            logger.warning(f"  ✗ Failed to upload '{event_summary}': {e}")
            return False

    @retry_on_failure(retries=2, delay=1)
    def _save_event_with_retry(self, calendar, event_ics):
        """Save event to calendar with retry."""
        try:
            calendar.save_event(event_ics)
        except (caldav.error.AuthorizationError, ConnectionError):
            # Force reset on connection/auth errors
            self._reset_connection()
            # Re-fetch calendar to ensure valid connection
            calendar = self.get_calendar()
            calendar.save_event(event_ics)

    @retry_on_failure(retries=2, delay=1)
    def list_calendars(self) -> List[str]:
        """List all available calendars."""
        calendars = self.principal.calendars()
        calendar_names = [cal.name for cal in calendars]
        logger.info(f"Found {len(calendar_names)} calendars: {calendar_names}")
        return calendar_names
    
    @retry_on_failure(retries=2, delay=1)
    def delete_old_events(self, days_to_keep: int = 90) -> int:
        """Remove events older than specified days."""
        logger.info(f"Cleaning up events older than {days_to_keep} days")
        
        calendar = self.get_calendar()
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        events = calendar.events()
        removed_count = 0
        
        for event in events:
            try:
                event_data = event.icalendar_component
                # Basic check for dtend - complex recurrence rules not handled here
                if hasattr(event_data, 'dtend'):
                    dt = event_data.dtend.dt
                    # Handle both naive and aware datetimes if needed
                    if dt.replace(tzinfo=None) < cutoff_date.replace(tzinfo=None):
                        event.delete()
                        removed_count += 1
            except Exception as e:
                logger.warning(f"Could not process event for deletion: {e}")
        
        logger.info(f"✓ Cleanup complete. Removed {removed_count} old events")
        return removed_count
    
    def close(self):
        """Close connection."""
        self._reset_connection()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
