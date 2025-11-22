"""Configuration management for MOTD bot."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Bot configuration from environment variables."""

    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

    # Scheduling
    DAILY_POST_HOUR = int(os.getenv('DAILY_POST_HOUR', '9'))
    DAILY_POST_MINUTE = int(os.getenv('DAILY_POST_MINUTE', '0'))
    TIMEZONE = os.getenv('TIMEZONE', 'UTC')

    # Testing
    DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'

    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'motd.db')

    # Data files
    PERSONALITY_FILE = 'data/kaine_personality.md'
    POSTS_FILE = 'data/mrkainez_posts.json'

    # Message history
    HISTORY_DAYS = 365

    # Similarity threshold for message uniqueness (0-1)
    # 0.85 means reject messages that are >85% similar to recent messages
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.85'))

    # Number of generation attempts before accepting best message
    MAX_GENERATION_ATTEMPTS = int(os.getenv('MAX_GENERATION_ATTEMPTS', '5'))

    # Days of history to check for similarity (default 90)
    # Lower = faster checks, higher = stricter uniqueness over longer period
    SIMILARITY_CHECK_DAYS = int(os.getenv('SIMILARITY_CHECK_DAYS', '90'))

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        errors = []

        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")

        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")

        if not cls.TELEGRAM_CHANNEL_ID:
            errors.append("TELEGRAM_CHANNEL_ID is required")

        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True
