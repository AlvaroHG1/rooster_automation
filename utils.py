"""
Shared utilities for Rooster Automation.
"""

import logging
import time
import functools
from typing import Callable, Type, Tuple, Optional

logger = logging.getLogger(__name__)

def retry_on_failure(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to retry a function on failure.
    
    Args:
        retries: Number of times to retry.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each failure.
        exceptions: Tuple of exceptions to catch and retry on.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < retries:
                        logger.warning(
                            f"Function '{func.__name__}' failed: {e}. "
                            f"Retrying in {current_delay:.1f}s (Attempt {attempt + 1}/{retries})"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"Function '{func.__name__}' failed after {retries} retries.")
            
            if last_exception:
                raise last_exception
        return wrapper
    return decorator

def setup_logging(level_name: str, format_str: str, file_path: str):
    """
    Configure logging for the application.
    """
    level = getattr(logging, level_name.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.FileHandler(file_path),
            logging.StreamHandler()
        ]
    )
