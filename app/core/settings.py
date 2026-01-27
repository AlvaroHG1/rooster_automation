"""
Configuration management for Rooster Automation.
Loads settings from environment variables and config.yaml.
"""

import os
import logging
import yaml
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Centralized settings management."""
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from yaml file."""
        # Config is now in ../../config/config.yaml relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        default_config_path = os.path.join(base_dir, 'config', 'config.yaml')
        
        config_path = os.getenv('CONFIG_PATH', default_config_path)
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        except Exception as e:
            logging.error(f"Failed to load config from {config_path}: {e}")
            raise

    # ROI Online Settings
    @property
    def roi_url(self) -> str:
        return self._config['roi_online']['url']

    @property
    def roi_username_field(self) -> str:
        return self._config['roi_online']['username_field_id']

    @property
    def roi_password_field(self) -> str:
        return self._config['roi_online']['password_field_id']

    @property
    def roi_login_button(self) -> str:
        return self._config['roi_online']['login_button_id']
    
    @property
    def roi_month_radio(self) -> str:
        return self._config['roi_online']['month_radio_button_id']
    
    @property
    def roi_calendar_export_button(self) -> str:
        return self._config['roi_online']['calendar_export_button_id']

    @property
    def roi_week_display(self) -> str:
        return self._config['roi_online']['week_display_id']

    @property
    def roi_prev_week_button(self) -> str:
        return self._config['roi_online']['prev_week_button_id']

    @property
    def roi_next_week_button(self) -> str:
        return self._config['roi_online']['next_week_button_id']

    @property
    def roi_email(self) -> str:
        val = os.getenv('ROI_EMAIL')
        if not val:
            raise ValueError("ROI_EMAIL environment variable is not set")
        return val

    @property
    def roi_password(self) -> str:
        val = os.getenv('ROI_PASSWORD')
        if not val:
            raise ValueError("ROI_PASSWORD environment variable is not set")
        return val

    # Gmail Settings
    @property
    def gmail_check_interval(self) -> int:
        return self._config['gmail'].get('check_interval_minutes', 10) * 60  # Convert to seconds

    @property
    def gmail_address(self) -> str:
        val = os.getenv('GMAIL_ADDRESS')
        if not val:
            raise ValueError("GMAIL_ADDRESS environment variable is not set")
        return val

    @property
    def gmail_app_password(self) -> str:
        val = os.getenv('GMAIL_APP_PASSWORD')
        if not val:
            raise ValueError("GMAIL_APP_PASSWORD environment variable is not set")
        return val
    
    @property
    def trigger_sender(self) -> str:
        return os.getenv('TRIGGER_EMAIL_SENDER', 'noreply@staff.nl')

    # Schedule Settings
    @property
    def active_day(self) -> str:
        return self._config['schedule']['active_day'].lower()

    @property
    def start_hour(self) -> int:
        return self._config['schedule']['start_hour']

    @property
    def end_hour(self) -> int:
        return self._config['schedule']['end_hour']

    # CalDAV Settings
    @property
    def caldav_url(self) -> str:
        val = os.getenv('CALDAV_URL')
        if not val:
            raise ValueError("CALDAV_URL environment variable is not set")
        return val

    @property
    def caldav_username(self) -> str:
        val = os.getenv('CALDAV_USERNAME')
        if not val:
            raise ValueError("CALDAV_USERNAME environment variable is not set")
        return val

    @property
    def caldav_password(self) -> str:
        val = os.getenv('CALDAV_PASSWORD')
        if not val:
            raise ValueError("CALDAV_PASSWORD environment variable is not set")
        return val

    @property
    def caldav_calendar_name(self) -> str:
        return os.getenv('CALDAV_CALENDAR_NAME', 'Rooster')

    # Logging Settings
    @property
    def logging_level(self) -> str:
        return self._config['logging'].get('level', 'INFO')

    @property
    def logging_format(self) -> str:
        return self._config['logging'].get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    @property
    def logging_file(self) -> str:
        return self._config['logging'].get('file', 'rooster_automation.log')

# Global settings instance
settings = Settings()
