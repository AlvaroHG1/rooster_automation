"""
File Storage Module
Handles saving .ics files to shared folder for iPhone Shortcuts automation.
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FileStorage:
    """Manages .ics file storage in shared folder."""
    
    def __init__(self):
        """Initialize file storage with shared folder path from environment."""
        self.shared_folder = os.getenv('SHARED_FOLDER_PATH')
        
        if not self.shared_folder:
            raise ValueError("SHARED_FOLDER_PATH must be set in environment variables")
        
        # Create folder if it doesn't exist
        Path(self.shared_folder).mkdir(parents=True, exist_ok=True)
        logger.info(f"Using shared folder: {self.shared_folder}")
    
    def save_ics_file(self, source_path: str) -> str:
        """
        Copy .ics file to shared folder.
        
        Args:
            source_path: Path to the source .ics file
            
        Returns:
            Path to the file in shared folder
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Get filename from source
        filename = os.path.basename(source_path)
        destination = os.path.join(self.shared_folder, filename)
        
        # Copy file
        logger.info(f"Copying {source_path} to {destination}")
        shutil.copy2(source_path, destination)
        
        logger.info(f"✓ File saved to shared folder: {destination}")
        return destination
    
    def cleanup_old_files(self, days_to_keep: int = 90):
        """
        Remove .ics files older than specified days.
        
        Args:
            days_to_keep: Number of days to keep files (default: 90)
        """
        logger.info(f"Cleaning up files older than {days_to_keep} days")
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        for filename in os.listdir(self.shared_folder):
            if not filename.endswith('.ics'):
                continue
            
            filepath = os.path.join(self.shared_folder, filename)
            
            # Get file modification time
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            if file_mtime < cutoff_date:
                logger.info(f"Removing old file: {filename}")
                os.remove(filepath)
                removed_count += 1
        
        logger.info(f"✓ Cleanup complete. Removed {removed_count} old files")
    
    def list_files(self) -> list:
        """
        List all .ics files in shared folder.
        
        Returns:
            List of .ics filenames
        """
        files = [f for f in os.listdir(self.shared_folder) if f.endswith('.ics')]
        return sorted(files)


class CalDAVStorage:
    """Manages .ics file upload to CalDAV server (e.g., iCloud Calendar)."""
    
    def __init__(self):
        """Initialize CalDAV storage with server credentials from environment."""
        import caldav
        from caldav.elements import dav
        
        self.caldav_url = os.getenv('CALDAV_URL')
        self.caldav_username = os.getenv('CALDAV_USERNAME')
        self.caldav_password = os.getenv('CALDAV_PASSWORD')
        self.calendar_name = os.getenv('CALDAV_CALENDAR_NAME', 'Rooster')
        
        if not all([self.caldav_url, self.caldav_username, self.caldav_password]):
            raise ValueError(
                "CALDAV_URL, CALDAV_USERNAME, and CALDAV_PASSWORD must be set in environment variables"
            )
        
        # Connect to CalDAV server
        logger.info(f"Connecting to CalDAV server: {self.caldav_url}")
        try:
            self.client = caldav.DAVClient(
                url=self.caldav_url,
                username=self.caldav_username,
                password=self.caldav_password
            )
            self.principal = self.client.principal()
            logger.info("✓ Successfully connected to CalDAV server")
        except Exception as e:
            logger.error(f"Failed to connect to CalDAV server: {e}")
            raise
    
    def get_calendar(self):
        """
        Get or create the calendar for storing roster events.
        
        Returns:
            Calendar object
        """
        calendars = self.principal.calendars()
        
        # Try to find existing calendar by name
        for cal in calendars:
            if cal.name == self.calendar_name:
                logger.info(f"Found existing calendar: {self.calendar_name}")
                return cal
        
        # If calendar doesn't exist, use the first available calendar
        if calendars:
            logger.warning(
                f"Calendar '{self.calendar_name}' not found. Using first available calendar: {calendars[0].name}"
            )
            return calendars[0]
        
        raise ValueError("No calendars found on CalDAV server")
    
    def save_ics_file(self, source_path: str) -> str:
        """
        Upload .ics file content to CalDAV server.
        
        Args:
            source_path: Path to the source .ics file
            
        Returns:
            Success message with calendar name
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Read .ics file content
        with open(source_path, 'r', encoding='utf-8') as f:
            ics_content = f.read()
        
        # Get calendar
        calendar = self.get_calendar()
        
        # Upload events to calendar
        logger.info(f"Uploading events from {source_path} to calendar '{calendar.name}'")
        
        try:
            # Save the entire .ics file as events in the calendar
            calendar.save_event(ics_content)
            logger.info(f"✓ Successfully uploaded events to calendar '{calendar.name}'")
            return f"Events uploaded to calendar: {calendar.name}"
        except Exception as e:
            logger.error(f"Failed to upload events: {e}")
            raise
    
    def list_calendars(self) -> list:
        """
        List all available calendars on the CalDAV server.
        
        Returns:
            List of calendar names
        """
        calendars = self.principal.calendars()
        calendar_names = [cal.name for cal in calendars]
        logger.info(f"Found {len(calendar_names)} calendars: {calendar_names}")
        return calendar_names
    
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


def main():
    """Test function to run file storage standalone."""
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    storage = FileStorage()
    
    print(f"Shared folder: {storage.shared_folder}")
    print(f"\nCurrent .ics files:")
    for file in storage.list_files():
        filepath = os.path.join(storage.shared_folder, file)
        size = os.path.getsize(filepath)
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
        print(f"  - {file} ({size} bytes, modified: {mtime})")


if __name__ == "__main__":
    main()
