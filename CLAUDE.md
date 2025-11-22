# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Telegram bot that posts daily "Message of the Day" (MOTD) messages as Mr. Kaine, creator of Zenon Network. The bot uses OpenAI to generate authentic messages based on personality guidelines and historical Telegram posts, posts them to a Telegram channel on schedule, and responds to `/motd` commands.

## Development Setup

### Initial Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys and settings
```

### Running the Bot
```bash
# Activate venv if not already active
source venv/bin/activate

# Run the bot
python motd_bot.py

# Run tests
python test_motd.py all           # Run all tests
python test_motd.py config        # Test configuration only
python test_motd.py generate      # Test message generation
python test_motd.py save          # Generate and save today's message
```

## Project Structure

```
motd-bot/
├── venv/                      # Virtual environment (gitignored)
├── data/
│   ├── kaine_personality.md   # Personality guidelines for message generation
│   └── mrkainez_posts.json    # Historical Telegram posts (882 messages, 499KB)
├── motd_bot.py               # Main bot application
├── message_generator.py      # OpenAI integration for message generation
├── database.py              # SQLite database for message history
├── config.py                # Configuration management
├── test_motd.py             # Local testing script
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variable template
└── .gitignore
```

## Core Components

### `motd_bot.py` - Main Bot
- Telegram bot with command handlers (`/start`, `/motd`)
- Scheduled daily posting using APScheduler
- Integrates database and message generator
- Handles dry-run mode for testing

### `message_generator.py` - OpenAI Integration
- Loads personality guidelines and post context
- Generates unique daily messages using GPT-4
- Validates message quality (length, structure)
- Retry logic with validation

### `database.py` - Message History
- SQLite storage for up to 365 days of messages
- Duplicate detection via content hashing
- Auto-cleanup of messages older than 365 days
- Query by date or retrieve recent messages

### `config.py` - Configuration
- Loads from environment variables (.env)
- Validates required settings
- Provides defaults for optional settings

### `test_motd.py` - Local Testing
- Test configuration, database, and message generation
- Generate messages without posting to Telegram
- Useful for development and debugging

## Data Files

### `data/kaine_personality.md`
Personality guidelines for Mr. Kaine:
- **Core traits**: Technical/analytical, visionary/philosophical, direct/no-nonsense
- **Message themes**: Technical insights, philosophical reflections, community motivation, critical observations
- **Message structure**: Two parts separated by blank line
  - Part 1: Main message (2-4 sentences)
  - Part 2: Contributor thanks (1-2 sentences)
- **Contributor appreciation**: Thanks to those who **actually work**
  - ✅ Developers, community managers, architects, researchers, shitposters on X
  - ❌ NOT node operators (they get emission rewards, mostly passive)
- **Voice examples**: Technical discussions, visionary statements, direct critiques, genuine appreciation

### `data/mrkainez_posts.json`
882 historical Telegram posts from @mrkainez:
- **Size**: 499KB, ~16K lines
- **Fields**: message_id, date, content, telegram_url, user info
- **Usage**: Sampled for context in message generation (every 10th post to reduce token usage)
- **Date range**: October 2021 onwards

## Bot Features

### Daily Auto-Posting
- Scheduled at configured time (default: 09:00 UTC)
- Generates unique message if none exists for today
- Checks against last 365 days to avoid repetition
- Posts to configured Telegram channel
- Auto-cleans up messages older than 365 days

### `/motd` Command
- Returns today's message on demand
- Uses cached message if already generated
- Generates new message if needed
- Available to any user in channels/groups where bot is present

### Message Generation
- Uses OpenAI GPT-4 with personality context
- Samples historical posts for authentic voice
- Validates uniqueness against database
- Includes rotating themes and contributor appreciation
- Retry logic for quality assurance

## Configuration

Required environment variables (see `.env.example`):
- `OPENAI_API_KEY` - OpenAI API key for GPT-4
- `TELEGRAM_BOT_TOKEN` - Telegram bot token from @BotFather
- `TELEGRAM_CHANNEL_ID` - Channel username (e.g., @zenon_motd) or chat ID

Optional settings:
- `DAILY_POST_HOUR` / `DAILY_POST_MINUTE` - Posting schedule (default: 09:00)
- `TIMEZONE` - Timezone for scheduling (default: UTC)
- `DRY_RUN` - Set to `true` to test without posting (default: false)
- `DATABASE_PATH` - SQLite database location (default: motd.db)

## Testing

The bot includes comprehensive testing capabilities:

1. **Configuration Test**: Verify all environment variables are set correctly
2. **Database Test**: Check database connectivity and existing messages
3. **Generation Test**: Generate a message and validate it
4. **Save Test**: Generate and save today's message to database

Use `DRY_RUN=true` in `.env` to test the full bot without actually posting to Telegram.

## Message History Management

- Messages stored in SQLite database with date, content, hash, and embedding vector
- Maximum 365 days of history maintained
- **Semantic similarity checking**: Uses OpenAI embeddings to ensure new messages are sufficiently different
  - Calculates cosine similarity between new message and last 90 days of messages
  - Default threshold: 0.85 (rejects messages >85% similar)
  - Configurable via `SIMILARITY_THRESHOLD` environment variable
- Exact duplicate detection via SHA-256 hashing (backup check)
- Automatic cleanup on each daily post
- One message per day maximum (cached if generated early)

## How Uniqueness Works

1. **Text Context**: Previous messages passed to GPT-4 prompt for awareness
2. **Embedding Similarity**: New messages compared against last 90 days using cosine similarity
3. **Retry Logic**: If similarity > threshold, regenerate with up to 3 attempts
4. **Threshold Control**: Adjust `SIMILARITY_THRESHOLD` (0-1) for strictness
   - 0.85 = reject if >85% similar (default, recommended)
   - 0.90 = more lenient, allows more similar messages
   - 0.80 = stricter, requires more unique messages
