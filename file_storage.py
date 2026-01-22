"""
File Storage Module
Handles saving .ics files to shared folder for iPhone Shortcuts automation.
"""

import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CalDAVStorage:
    """Manages .ics file upload to CalDAV server (e.g., iCloud Calendar)."""
    
    def __init__(self):
        """Initialize CalDAV storage with server credentials from environment."""
        # Store credentials but don't connect yet (lazy connection pattern)
        self.caldav_url = os.getenv('CALDAV_URL')
        self.caldav_username = os.getenv('CALDAV_USERNAME')
        self.caldav_password = os.getenv('CALDAV_PASSWORD')
        self.calendar_name = os.getenv('CALDAV_CALENDAR_NAME', 'Rooster')
        
        # Private connection state
        self._client = None
        self._principal = None
        self._calendar_cache = None
        
        # Validate credentials are present
        if not all([self.caldav_url, self.caldav_username, self.caldav_password]):
            raise ValueError(
                "CALDAV_URL, CALDAV_USERNAME, and CALDAV_PASSWORD must be set in environment variables"
            )
        
        logger.info(f"CalDAV storage initialized (connection will be established when needed)")
    
    @property
    def client(self):
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
    
    def _connect(self):
        """Establish connection to CalDAV server with retry logic."""
        import caldav
        import time
        
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to CalDAV server: {self.caldav_url} (attempt {attempt + 1}/{max_retries})")
                
                self._client = caldav.DAVClient(
                    url=self.caldav_url,
                    username=self.caldav_username,
                    password=self.caldav_password
                )
                
                # Test connection by getting principal
                self._principal = self._client.principal()
                
                logger.info("✓ Successfully connected to CalDAV server")
                return
                
            except (ConnectionError, ConnectionResetError, TimeoutError) as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    self._reset_connection()
                else:
                    logger.error(f"Failed to connect after {max_retries} attempts")
                    raise ConnectionError(f"Could not connect to CalDAV server: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error during connection: {e}")
                raise
    
    def _reset_connection(self):
        """Reset connection state."""
        self._client = None
        self._principal = None
        self._calendar_cache = None
        logger.debug("Connection state reset")
    
    def _execute_with_retry(self, operation, *args, **kwargs):
        """
        Execute a CalDAV operation with automatic retry on connection errors.
        
        Args:
            operation: Function to execute
            *args, **kwargs: Arguments for the operation
        
        Returns:
            Result of the operation
        """
        import requests
        import time
        
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
                
            except (ConnectionError, ConnectionResetError, requests.exceptions.ConnectionError) as e:
                logger.warning(f"Operation failed due to connection error: {e}")
                
                if attempt < max_retries - 1:
                    logger.info("Resetting connection and retrying...")
                    self._reset_connection()
                    time.sleep(1)
                else:
                    logger.error("Operation failed after all retry attempts")
                    raise
            
            except Exception as e:
                # Don't retry on other errors
                raise

    def get_calendar(self):
        """
        Get or find the calendar for storing roster events.
        
        Returns:
            Calendar object
        """
        # Check cache first
        if self._calendar_cache is not None:
            return self._calendar_cache
        
        def _get_calendar_internal():
            calendars = self.principal.calendars()
            
            # Try to find existing calendar by name
            for cal in calendars:
                if cal.name == self.calendar_name:
                    logger.info(f"Found calendar: {self.calendar_name}")
                    return cal
            
            # Fallback to first available calendar
            if calendars:
                logger.warning(
                    f"Calendar '{self.calendar_name}' not found. "
                    f"Using first available: {calendars[0].name}"
                )
                return calendars[0]
            
            raise ValueError("No calendars found on CalDAV server")
        
        # Execute with retry and cache result
        self._calendar_cache = self._execute_with_retry(_get_calendar_internal)
        return self._calendar_cache
    
    def save_ics_file(self, source_path: str) -> str:
        """
        Upload .ics file content to CalDAV server.
        Parses the .ics file and uploads each event individually.
        
        Args:
            source_path: Path to the source .ics file
            
        Returns:
            Success message with calendar name and event count
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Parse .ics file using icalendar
        from icalendar import Calendar
        
        logger.info(f"Reading .ics file: {source_path}")
        with open(source_path, 'rb') as f:
            cal = Calendar.from_ical(f.read())
        
        # Get calendar with retry
        calendar = self.get_calendar()
        
        # Extract and upload individual events
        logger.info(f"Uploading events to calendar: {calendar.name}")
        
        events_uploaded = 0
        events_failed = 0
        failed_events = []
        
        for component in cal.walk():
            if component.name == "VEVENT":
                event_summary = component.get('SUMMARY', 'No title')
                event_start = component.get('DTSTART')
                
                try:
                    # Convert individual event back to iCalendar format
                    event_cal = Calendar()
                    # Copy calendar properties (like VERSION, PRODID)
                    for key in cal.keys():
                        if key not in ['VEVENT']:
                            event_cal.add(key, cal[key])
                    # Add the individual event
                    event_cal.add_component(component)
                    
                    # Upload this individual event with retry
                    event_ics = event_cal.to_ical().decode('utf-8')
                    
                    def _upload_event():
                        calendar.save_event(event_ics)
                    
                    self._execute_with_retry(_upload_event)
                    
                    events_uploaded += 1
                    logger.debug(f"  ✓ Uploaded: {event_summary} (starts: {event_start})")
                    
                except Exception as e:
                    events_failed += 1
                    failed_events.append({
                        'summary': event_summary,
                        'start': str(event_start),
                        'error': str(e)
                    })
                    logger.warning(f"  ✗ Failed to upload '{event_summary}': {e}")
        
        # Log summary
        logger.info(f"Upload complete: {events_uploaded} succeeded, {events_failed} failed")
        
        if events_uploaded == 0:
            raise ValueError("No events were successfully uploaded from the .ics file")
        
        if failed_events:
            logger.warning(f"Failed events: {len(failed_events)} total")
            for evt in failed_events[:3]:  # Log first 3 failures
                logger.debug(f"  - {evt['summary']}: {evt['error']}")
        
        return f"Uploaded {events_uploaded} events to calendar: {calendar.name}"
    
    def list_calendars(self) -> list:
        """
        List all available calendars on the CalDAV server.
        
        Returns:
            List of calendar names
        """
        def _list_calendars_internal():
            calendars = self.principal.calendars()
            calendar_names = [cal.name for cal in calendars]
            logger.info(f"Found {len(calendar_names)} calendars: {calendar_names}")
            return calendar_names
        
        return self._execute_with_retry(_list_calendars_internal)
    
    def delete_old_events(self, days_to_keep: int = 90):
        """
        Remove events older than specified days from the calendar.
        
        Args:
            days_to_keep: Number of days to keep events (default: 90)
        """
        from datetime import datetime, timedelta
        
        logger.info(f"Cleaning up events older than {days_to_keep} days")
        
        calendar = self.get_calendar()
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        def _delete_old_events_internal():
            # Get all events
            events = calendar.events()
            removed_count = 0
            
            for event in events:
                try:
                    # Get event data
                    event_data = event.icalendar_component
                    
                    # Check if event has ended before cutoff date
                    if hasattr(event_data, 'dtend') and event_data.dtend.dt < cutoff_date:
                        event.delete()
                        removed_count += 1
                except Exception as e:
                    logger.warning(f"Could not process event: {e}")
                    continue
            
            logger.info(f"✓ Cleanup complete. Removed {removed_count} old events")
            return removed_count
        
        return self._execute_with_retry(_delete_old_events_internal)
    
    def close(self):
        """Close CalDAV connection and cleanup resources."""
        if self._client is not None:
            try:
                logger.debug("Closing CalDAV connection")
                self._reset_connection()
            except Exception as e:
                logger.warning(f"Error during connection cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()
        return False
    
    def test_connection(self) -> bool:
        """
        Test if CalDAV connection is working.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            # Force fresh connection
            self._reset_connection()
            
            # Try to get calendars
            calendars = self.principal.calendars()
            
            logger.info(f"✓ Connection test successful. Found {len(calendars)} calendars")
            return True
            
        except Exception as e:
            logger.error(f"✗ Connection test failed: {e}")
            return False
