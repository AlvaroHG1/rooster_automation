import logging
import sys
from typing import Optional

def setup_logging(level_name: str = "INFO", format_str: Optional[str] = None, file_path: str = "rooster_automation.log") -> None:
    """
    Configure logging for the application using a centralized setup.
    
    Args:
        level_name: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_str: Optional custom format string
        file_path: Path to the log file
    """
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
    level = getattr(logging, level_name.upper(), logging.INFO)
    
    # Remove existing handlers to avoid duplication if called multiple times
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.FileHandler(file_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set third-party loggers to warning to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
