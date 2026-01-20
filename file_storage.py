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
