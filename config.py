import os
from dotenv import load_dotenv
from datetime import datetime
import ast

load_dotenv()

class Config:
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "job_automation")

    # Search Parameters
    SEARCH_KEYWORDS = [kw.strip() for kw in os.getenv("SEARCH_KEYWORDS", "Python Developer").split(",")]
    LOCATION = os.getenv("LOCATION", "Karachi, Pakistan")

    # Application Limits
    MAX_APPLICATIONS_PER_DAY = int(os.getenv("MAX_APPLICATIONS_PER_DAY", 30))
    DAILY_RESET_HOUR = int(os.getenv("DAILY_RESET_HOUR", 0))

    # Browser & Scraping
    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
    STEALTH_ENABLED = os.getenv("STEALTH_ENABLED", "true").lower() == "true"
    RANDOM_DELAY_MIN = float(os.getenv("RANDOM_DELAY_MIN", 3.0))
    RANDOM_DELAY_MAX = float(os.getenv("RANDOM_DELAY_MAX", 8.0))

    # Email
    GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")
    GMAIL_SCOPES = [os.getenv("GMAIL_SCOPES", "https://mail.google.com/")]

    # Paths
    DATA_DIR = os.getenv("DATA_DIR", "data")
    CSV_FILE = os.getenv("CSV_FILE", "data/jobs.csv")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @staticmethod
    def ensure_directories():
        """Create necessary directories if they do not exist."""
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(Config.CSV_FILE), exist_ok=True)

    @staticmethod
    def get_today_key():
        """Returns a string key for daily tracking (e.g., '2026-04-18')."""
        return datetime.utcnow().strftime("%Y-%m-%d")