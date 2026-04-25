import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent


class Config:
    # Paths
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    SESSIONS_DIR = BASE_DIR / "data" / "sessions"
    RESUME_TAILORED_DIR = BASE_DIR / "data" / "resume_tailored"
    DB_PATH = BASE_DIR / "data" / "jobhunterx.db"
    RESUME_BASE_PATH = BASE_DIR / "data" / "resume_base.pdf"
    PROFILE_PATH = BASE_DIR / "data" / "profile.json"
    MNC_LIST_PATH = BASE_DIR / "data" / "mnc_list.json"

    # Platform credentials
    NAUKRI_EMAIL = os.getenv("NAUKRI_EMAIL", "")
    NAUKRI_PASSWORD = os.getenv("NAUKRI_PASSWORD", "")
    LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
    LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")
    INDEED_EMAIL = os.getenv("INDEED_EMAIL", "")
    INDEED_PASSWORD = os.getenv("INDEED_PASSWORD", "")
    INTERNSHALA_EMAIL = os.getenv("INTERNSHALA_EMAIL", "")
    INTERNSHALA_PASSWORD = os.getenv("INTERNSHALA_PASSWORD", "")

    # AI
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL = "claude-sonnet-4-6"

    # Email
    GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")

    # Email discovery
    HUNTER_IO_API_KEY = os.getenv("HUNTER_IO_API_KEY", "")
    APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")

    # Dashboard
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8080"))
    SECRET_KEY = os.getenv("SECRET_KEY", "changeme-use-a-real-32-char-secret")

    # Search keywords
    SEARCH_KEYWORDS = [
        "generative ai engineer",
        "llm engineer",
        "ml engineer",
        "ai product manager",
        "nlp engineer",
        "deep learning engineer",
        "large language model",
        "ai engineer",
    ]

    # Scheduler intervals
    SCRAPE_INTERVAL_HOURS = 2
    SCORE_INTERVAL_MINUTES = 30
    APPLY_INTERVAL_MINUTES = 5
    COLD_EMAIL_HOUR = 9
    RETRY_INTERVAL_HOURS = 1
    SESSION_REFRESH_HOURS = 6
    SESSION_HEALTH_INTERVAL_MINUTES = 10

    # Rate limits (per day)
    MAX_APPLICATIONS_PER_DAY = 50
    COLD_EMAILS_PER_DAY = 20
    LINKEDIN_MAX_DAILY = 30
    NAUKRI_MAX_DAILY = 50
    INDEED_MAX_DAILY = 40
    INTERNSHALA_MAX_DAILY = 20

    # Scoring thresholds
    AUTO_REJECT_BELOW = 40
    MIN_SHOW_SCORE = 40

    # Retry
    MAX_RETRIES = 3

    # Delays (seconds)
    MIN_ACTION_DELAY = 2.0
    MAX_ACTION_DELAY = 5.0


config = Config()
