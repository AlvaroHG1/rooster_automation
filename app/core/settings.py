"""
Configuration management for Rooster Automation.
Uses Pydantic for validation and type safety.
"""

import os
import yaml
import logging
from typing import List, Optional, Union, Literal
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the project base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

class RoiOnlineSettings(BaseModel):
    url: str
    username_field_id: str
    password_field_id: str
    login_button_id: str
    month_radio_button_id: str
    calendar_export_button_id: str
    week_display_id: str
    prev_week_button_id: str
    next_week_button_id: str
    
    # Secrets from Env
    email: str = Field(..., description="ROI_EMAIL from env")
    password: str = Field(..., description="ROI_PASSWORD from env")

class GmailSettings(BaseModel):
    check_interval_minutes: int = 10
    max_emails_to_check: int = 10
    
    # Secrets from Env
    address: str = Field(..., description="GMAIL_ADDRESS from env")
    app_password: str = Field(..., description="GMAIL_APP_PASSWORD from env")
    trigger_sender: str = "noreply@staff.nl"

class ScheduleSettings(BaseModel):
    active_days: List[str] = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    start_hour: int = 10
    end_hour: int = 18

    @field_validator('active_days', mode='before')
    @classmethod
    def normalize_active_days(cls, v):
        if isinstance(v, str):
            return [v.lower()]
        if isinstance(v, list):
            return [d.lower() for d in v]
        return v

class CalDavSettings(BaseModel):
    url: str
    username: str
    password: str
    calendar_name: str = "Rooster"

class LoggingSettings(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "rooster_automation.log"

class Settings(BaseSettings):
    """
    Main Settings Class.
    Combines environment variables and YAML config.
    """
    roi_online: RoiOnlineSettings
    gmail: GmailSettings
    schedule: ScheduleSettings
    caldav: CalDavSettings
    logging: LoggingSettings
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @classmethod
    def load(cls) -> "Settings":
        """
        Load settings from YAML and Environment variables.
        """
        # 1. Load YAML content
        yaml_config = {}
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r") as f:
                    yaml_config = yaml.safe_load(f) or {}
            except Exception as e:
                logging.error(f"Failed to load config from {CONFIG_PATH}: {e}")
        
        # 2. Extract sections from YAML
        roi_yaml = yaml_config.get("roi_online", {})
        gmail_yaml = yaml_config.get("gmail", {})
        schedule_yaml = yaml_config.get("schedule", {})
        logging_yaml = yaml_config.get("logging", {})
        
        # 3. Merge with Environment Variables (Env vars take precedence/are required for secrets)
        # We construct the dictionaries to pass to the constructor
        
        # ROI
        roi_data = {
            **roi_yaml,
            "email": os.getenv("ROI_EMAIL", ""),
            "password": os.getenv("ROI_PASSWORD", "")
        }
        
        # Gmail
        gmail_data = {
            **gmail_yaml,
            "address": os.getenv("GMAIL_ADDRESS", ""),
            "app_password": os.getenv("GMAIL_APP_PASSWORD", ""),
            "trigger_sender": os.getenv("TRIGGER_EMAIL_SENDER", "noreply@staff.nl")
        }
        
        # Schedule
        # Handle the dynamic keys in YAML (active_day vs active_days)
        if "active_day" in schedule_yaml:
            schedule_yaml["active_days"] = schedule_yaml.pop("active_day")
        schedule_data = {**schedule_yaml}
        
        # CalDAV (Env dependent)
        caldav_data = {
            "url": os.getenv("CALDAV_URL", ""),
            "username": os.getenv("CALDAV_USERNAME", ""),
            "password": os.getenv("CALDAV_PASSWORD", ""),
            "calendar_name": os.getenv("CALDAV_CALENDAR_NAME", "Rooster")
        }
        
        # Logging
        logging_data = {**logging_yaml}
        
        return cls(
            roi_online=roi_data,
            gmail=gmail_data,
            schedule=schedule_data,
            caldav=caldav_data,
            logging=logging_data
        )

    # Proxy properties to maintain backward compatibility where possible
    # or to provide easy access
    
    @property
    def roi_url(self) -> str: return self.roi_online.url
    @property
    def roi_email(self) -> str: return self.roi_online.email
    @property
    def roi_password(self) -> str: return self.roi_online.password
    @property
    def roi_username_field(self) -> str: return self.roi_online.username_field_id
    @property
    def roi_password_field(self) -> str: return self.roi_online.password_field_id
    @property
    def roi_login_button(self) -> str: return self.roi_online.login_button_id
    @property
    def roi_month_radio(self) -> str: return self.roi_online.month_radio_button_id
    @property
    def roi_calendar_export_button(self) -> str: return self.roi_online.calendar_export_button_id
    @property
    def roi_week_display(self) -> str: return self.roi_online.week_display_id
    @property
    def roi_prev_week_button(self) -> str: return self.roi_online.prev_week_button_id
    @property
    def roi_next_week_button(self) -> str: return self.roi_online.next_week_button_id

    @property
    def gmail_check_interval(self) -> int: return self.gmail.check_interval_minutes * 60
    @property
    def gmail_address(self) -> str: return self.gmail.address
    @property
    def gmail_app_password(self) -> str: return self.gmail.app_password
    @property
    def trigger_sender(self) -> str: return self.gmail.trigger_sender

    @property
    def active_days(self) -> List[str]: return self.schedule.active_days
    @property
    def start_hour(self) -> int: return self.schedule.start_hour
    @property
    def end_hour(self) -> int: return self.schedule.end_hour

    @property
    def caldav_url(self) -> str: return self.caldav.url
    @property
    def caldav_username(self) -> str: return self.caldav.username
    @property
    def caldav_password(self) -> str: return self.caldav.password
    @property
    def caldav_calendar_name(self) -> str: return self.caldav.calendar_name

    @property
    def logging_level(self) -> str: return self.logging.level
    @property
    def logging_format(self) -> str: return self.logging.format
    @property
    def logging_file(self) -> str: return self.logging.file

# Global settings instance
try:
    settings = Settings.load()
except Exception as e:
    # Fallback/Error handling during import time if env vars are missing
    logging.error(f"Failed to load settings: {e}")
    # We might re-raise or allow it to fail later
    raise
