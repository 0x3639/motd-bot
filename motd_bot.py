"""
Zenon Network Message of the Day Bot
Generates and posts daily messages from Mr. Kaine to Telegram
"""
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import Config
from database import MessageDatabase
from message_generator import MessageGenerator

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class MOTDBot:
    """Message of the Day bot for Telegram."""

    def __init__(self):
        """Initialize the bot."""
        Config.validate()
        self.db = MessageDatabase()
        self.generator = MessageGenerator()
        self.application = None
        self.scheduler = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = (
            "Welcome to the Zenon Network Message of the Day bot!\n\n"
            "Commands:\n"
            "/motd - Get today's message\n"
            "/start - Show this welcome message"
        )
        await update.message.reply_text(welcome_message)

    async def motd_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /motd command - send today's message."""
        logger.info(f"MOTD command received from {update.effective_user.id}")

        # Check if we already have today's message (timezone-aware)
        tz = pytz.timezone(Config.TIMEZONE)
        today = datetime.now(tz).strftime('%Y-%m-%d')
        existing_message = self.db.get_message_by_date(today)

        if existing_message:
            logger.info("Returning cached message for today")
            await update.message.reply_text(existing_message)
        else:
            logger.info("Generating new message for today")
            await update.message.reply_text("Generating today's message...")

            # Generate new message
            message = await self.generate_daily_message()

            if message:
                await update.message.reply_text(message)
            else:
                await update.message.reply_text(
                    "Sorry, I encountered an error generating today's message. Please try again later."
                )

    async def generate_daily_message(self) -> str:
        """Generate today's message if it doesn't exist."""
        # Use timezone-aware date to match scheduler
        tz = pytz.timezone(Config.TIMEZONE)
        today = datetime.now(tz).strftime('%Y-%m-%d')

        # Check if message already exists for today
        existing_message = self.db.get_message_by_date(today)
        if existing_message:
            logger.info("Using existing message for today")
            return existing_message

        # Get recent messages for context (text only)
        recent_messages = self.db.get_recent_messages()
        logger.info(f"Retrieved {len(recent_messages)} recent messages for context")

        # Get recent embeddings for similarity checking
        recent_embeddings = self.db.get_recent_embeddings(days=Config.SIMILARITY_CHECK_DAYS)
        logger.info(f"Retrieved {len(recent_embeddings)} embeddings for similarity checking")

        # Generate new message with similarity checking
        logger.info(f"Generating new message (threshold: {Config.SIMILARITY_THRESHOLD:.2%}, max attempts: {Config.MAX_GENERATION_ATTEMPTS})...")
        message, embedding = self.generator.generate_with_retry(
            previous_messages=recent_messages,
            recent_embeddings=recent_embeddings,
            max_attempts=Config.MAX_GENERATION_ATTEMPTS,
            similarity_threshold=Config.SIMILARITY_THRESHOLD
        )

        if not message:
            logger.error("Failed to generate unique message after retries")
            return None

        # Save to database with embedding
        self.db.save_message(today, message, embedding)
        logger.info("Message generated and saved successfully")

        return message

    async def post_daily_message(self):
        """Post the daily message to the configured channel."""
        logger.info("Starting daily message posting job")

        # Clean up old messages first
        deleted = self.db.cleanup_old_messages()
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old messages")

        # Generate or retrieve today's message
        message = await self.generate_daily_message()

        if not message:
            logger.error("Could not generate message for posting")
            return

        # Post to Telegram if not in dry-run mode
        if Config.DRY_RUN:
            logger.info("DRY RUN MODE - Would have posted:")
            logger.info(message)
        else:
            try:
                await self.application.bot.send_message(
                    chat_id=Config.TELEGRAM_CHANNEL_ID,
                    text=message
                )
                logger.info(f"Message posted to {Config.TELEGRAM_CHANNEL_ID}")
            except Exception as e:
                logger.error(f"Error posting message to Telegram: {e}")

    def setup_scheduler(self, event_loop):
        """Set up the daily posting schedule."""
        self.scheduler = AsyncIOScheduler(
            timezone=pytz.timezone(Config.TIMEZONE),
            event_loop=event_loop
        )

        # Schedule daily post
        trigger = CronTrigger(
            hour=Config.DAILY_POST_HOUR,
            minute=Config.DAILY_POST_MINUTE,
            timezone=Config.TIMEZONE
        )

        self.scheduler.add_job(
            self.post_daily_message,
            trigger=trigger,
            id='daily_motd',
            name='Post daily MOTD',
            replace_existing=True
        )

        logger.info(
            f"Scheduled daily posts at {Config.DAILY_POST_HOUR:02d}:{Config.DAILY_POST_MINUTE:02d} {Config.TIMEZONE}"
        )

    async def post_init(self, application: Application):
        """Initialize bot after application setup."""
        self.application = application
        logger.info("Bot initialized successfully")

    def run(self):
        """Run the bot."""
        logger.info("Starting Zenon MOTD Bot...")

        # Create application
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("motd", self.motd_command))

        # Get event loop for scheduler (Python 3.14+ compatibility)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Set up scheduler with event loop
        self.setup_scheduler(loop)
        self.scheduler.start()

        # Run the bot
        logger.info("Bot is running. Press Ctrl+C to stop.")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point."""
    try:
        bot = MOTDBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == '__main__':
    main()
