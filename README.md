# Zenon Network - Message of the Day Bot

A Telegram bot that posts daily messages from Mr. Kaine, creator of Zenon Network. The bot uses OpenAI to generate authentic messages based on personality guidelines and 882 historical Telegram posts.

## Features

- 🤖 **Automated Daily Posts**: Posts at 5:00 AM Central Time to your Telegram channel
- 💬 **Interactive `/motd` Command**: Users can request today's message anytime, 24/7
- 🔄 **Semantic Uniqueness**: AI embeddings ensure messages are truly different, not just textually unique
- 🎯 **Authentic Voice**: Generated from Mr. Kaine's actual Telegram history
- 🙏 **Community Recognition**: Daily thanks to developers, researchers, community managers, architects, and shitposters
- 🐳 **Docker Ready**: Easy deployment with Docker Compose
- 📊 **Smart Safety**: Tracks best message across attempts, never fails to post
- 🔒 **Data Persistence**: Database survives restarts and reboots

---

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Bot Commands](#bot-commands)
- [How It Works](#how-it-works)
- [Docker Deployment](#docker-deployment)
- [Python Deployment](#python-deployment)
- [Testing](#testing)
- [Uniqueness & Safety](#uniqueness--safety)
- [Data Management](#data-management)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Docker (Recommended)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key and Telegram credentials

# 2. Build and start
docker-compose up -d

# 3. View logs
docker-compose logs -f

# 4. Test it works
docker-compose run --rm motd-bot python test_motd.py generate
```

That's it! Bot is running and will post daily at 5 AM Central Time.

---

## Configuration

### Required Environment Variables

Create `.env` file with:

```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHANNEL_ID=@your_channel_or_-chat_id

# Scheduling (5 AM Central Time)
DAILY_POST_HOUR=5
DAILY_POST_MINUTE=0
TIMEZONE=America/Chicago
```

### Optional Configuration

```env
# Testing mode (prevents actual posting)
DRY_RUN=false

# Uniqueness controls
SIMILARITY_THRESHOLD=0.85        # Reject if >85% similar (0-1)
MAX_GENERATION_ATTEMPTS=5        # Tries before using best message
SIMILARITY_CHECK_DAYS=90         # Days of history to check

# Database
DATABASE_PATH=motd.db
```

### Getting Telegram Credentials

1. **Create bot**: Message [@BotFather](https://t.me/botfather) → `/newbot` → Get `TELEGRAM_BOT_TOKEN`
2. **Create channel**: Create a new Telegram channel
3. **Add bot as admin**: Add bot to channel with "Post Messages" permission
4. **Get channel ID**: Use `@your_channel_name` or numeric chat ID (e.g., `-1001234567890`)

### Timezone Configuration

The bot uses `America/Chicago` (Central Time) which automatically handles Daylight Saving Time:
- **Winter (CST)**: 5:00 AM CST = 11:00 AM UTC
- **Summer (CDT)**: 5:00 AM CDT = 10:00 AM UTC

**Other US timezones:**
- Eastern: `America/New_York`
- Mountain: `America/Denver`
- Pacific: `America/Los_Angeles`
- Arizona (no DST): `America/Phoenix`

**International examples:**
- London: `Europe/London`
- Paris: `Europe/Paris`
- Tokyo: `Asia/Tokyo`
- Sydney: `Australia/Sydney`

---

## Bot Commands

### `/start`
Shows welcome message and available commands.

**Usage:** Send `/start` to the bot
**Available to:** Anyone who can message the bot

### `/motd`
Get today's message of the day on-demand.

**Usage:** Send `/motd` to the bot

**How it works:**
- If today's message exists (from scheduler or previous `/motd`) → Instant reply from cache
- If no message exists yet → Generates new message (~5-10 seconds), saves to DB, replies

**Available:** 24/7 to anyone who can message the bot

**Where:** Direct messages, group chats, channels (if bot has read permission)

---

## How It Works

### Scheduled Daily Posting

**Timeline:**
1. **5:00 AM Central Time**: Scheduler triggers
2. **Check database**: Is there already a message for today?
3. **Generate if needed**: Create new message using OpenAI
4. **Uniqueness check**: Compare against last 90 days using embeddings
5. **Save to database**: Store message with embedding vector
6. **Post to channel**: Send to configured Telegram channel

### On-Demand `/motd` Command

**Flow:**
1. **User sends `/motd`**
2. **Check database**: Already have today's message?
   - Yes → Reply instantly
   - No → Generate, save, reply
3. **User gets message** within 1-10 seconds

### Message Generation Process

1. **Load context**: 882 historical posts from Mr. Kaine
2. **Load personality**: Guidelines for voice, themes, contributor appreciation
3. **Get recent messages**: Last 365 days for text context
4. **Get embeddings**: Last 90 days for similarity checking
5. **Generate with GPT-4**: Create 2-part message (insight + thanks)
6. **Validate format**:
   - Blank line separates parts
   - Thanks doesn't mention node operators
   - 2+ sentences, proper length
7. **Check similarity**: Calculate cosine similarity to recent messages
   - If >85% similar → Retry (up to 5 attempts)
   - Track best message across attempts
8. **Fallback safety**: If all attempts exceed threshold, use least similar
9. **Generate embedding**: Create vector for future comparisons
10. **Save and return**: Store in database, send to user/channel

### Message Format

```
[Main Message - 2-4 sentences]
Technical insight, philosophical reflection, or critical observation
in Mr. Kaine's direct, no-nonsense voice.

[Contributor Thanks - 1-2 sentences]
Thanks to the developers, researchers, community managers, architects,
and shitposters who actually do the work.
```

**Who gets thanked:**
- ✅ Developers (writing code, building tools)
- ✅ Community Managers (organizing, moderating)
- ✅ Architects (designing systems)
- ✅ Researchers (exploring, testing, documenting)
- ✅ Shitposters on X (spreading awareness, memes)
- ❌ NOT node operators (they get emission rewards)

---

## Docker Deployment

### Starting the Bot

```bash
# Start in background
docker-compose up -d

# Start in foreground (see logs)
docker-compose up

# Rebuild and start (after code changes)
docker-compose up -d --build
```

### Managing the Bot

```bash
# View logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# Check status
docker-compose ps

# Restart
docker-compose restart

# Stop
docker-compose stop

# Stop and remove container
docker-compose down
```

### Testing in Docker

```bash
# Test configuration
docker-compose run --rm motd-bot python test_motd.py config

# Test message generation
docker-compose run --rm motd-bot python test_motd.py generate

# Generate and save today's message
docker-compose run --rm motd-bot python test_motd.py save

# Run all tests
docker-compose run --rm motd-bot python test_motd.py all
```

### Production Deployment

**Option 1: Docker on Server**

```bash
# Copy to server
scp -r motd-bot/ user@server:/path/to/

# SSH to server
ssh user@server
cd /path/to/motd-bot

# Configure and start
cp .env.example .env
nano .env  # Add your keys
docker-compose up -d

# Auto-start on reboot (add to crontab)
crontab -e
# Add: @reboot cd /path/to/motd-bot && docker-compose up -d
```

**Option 2: systemd Service (Linux)**

See [Python Deployment](#python-deployment) section.

---

## Python Deployment

### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd motd-bot

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env with your keys
```

### Running

```bash
# Activate venv
source venv/bin/activate

# Run bot
python motd_bot.py
```

### Running as systemd Service

Create `/etc/systemd/system/motd-bot.service`:

```ini
[Unit]
Description=Zenon MOTD Bot
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/motd-bot
Environment="PATH=/path/to/motd-bot/venv/bin"
ExecStart=/path/to/motd-bot/venv/bin/python motd_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable motd-bot
sudo systemctl start motd-bot
sudo systemctl status motd-bot

# View logs
sudo journalctl -u motd-bot -f
```

### Using screen/tmux

```bash
# Start screen session
screen -S motd-bot

# Activate venv and run
source venv/bin/activate
python motd_bot.py

# Detach: Ctrl+A then D
# Reattach: screen -r motd-bot
```

---

## Testing

### Test Suite

```bash
# All tests
python test_motd.py all

# Individual tests
python test_motd.py config      # Verify configuration
python test_motd.py database    # Test database operations
python test_motd.py generate    # Generate test message (no save)
python test_motd.py save        # Generate and save today's message
```

### Dry-Run Mode

Test without posting to Telegram:

```env
# In .env
DRY_RUN=true
```

Bot will:
- Generate messages normally
- Save to database
- Log what it would post
- NOT send to Telegram

### Manual Testing

```bash
# Generate a message
python test_motd.py generate

# Expected output:
# ✅ Message generated successfully!
# [Message with blank line separator]
# Validation: ✅ Passed
# Similarity check passed
```

---

## Uniqueness & Safety

### Multi-Layer Uniqueness

1. **Text Context**: Previous 365 days passed to GPT-4 for awareness
2. **Semantic Similarity**: OpenAI embeddings compare meaning
   - Checks last 90 days of messages
   - Calculates cosine similarity (0-1 scale)
   - Rejects if >85% similar (configurable)
3. **Exact Hash**: SHA-256 backup for perfect duplicates

### How Similarity Works

**Embeddings:** Messages converted to 1536-dimensional vectors capturing meaning

**Cosine Similarity:**
- 1.0 = Identical meaning
- 0.85 = Very similar (default rejection threshold)
- 0.70 = Somewhat similar (typically accepted)
- 0.50 = Different topics

**Example:**
```
Message A: "Decentralization isn't just a buzzword—it's a fundamental shift."
Message B: "True decentralization represents a fundamental paradigm shift."
Similarity: ~0.88 → Rejected as too similar
```

### Safety Mechanisms

**Problem:** What if bot can't generate a message below threshold?

**Solution:** Multi-layer safety net

1. **Track Best Message**: Saves least similar message across all attempts
2. **5 Retry Attempts**: Multiple chances to find unique message
3. **Intelligent Fallback**: After 5 attempts, uses best message even if above threshold
4. **Never Fails**: Always posts a message (unless API is completely down)

**Example Log:**
```
Attempt 1: Message too similar (similarity: 88.23%)
Attempt 2: Message too similar (similarity: 87.45%)
Attempt 3: Message too similar (similarity: 86.91%)
Attempt 4: Message too similar (similarity: 86.12%)
Attempt 5: Message too similar (similarity: 85.67%)
⚠️  Using best message from 5 attempts (similarity: 85.67%)
Message posted successfully
```

### Adjusting Strictness

As message history grows over months, you may need to relax the threshold:

```env
# After 6+ months, consider:
SIMILARITY_THRESHOLD=0.87

# After 1+ year:
SIMILARITY_THRESHOLD=0.90
```

---

## Data Management

### Database Persistence

**Location:** `./data/motd.db` (on host machine, not in container)

**Persists across:**
- ✅ Container restarts
- ✅ System reboots
- ✅ Docker updates
- ✅ Image rebuilds

**Lost only if:**
- You manually delete the file
- You run `docker-compose down -v` (⚠️ WARNING: deletes volumes)

### What Gets Stored

```
messages table:
├── id (auto-increment)
├── date (YYYY-MM-DD, unique)
├── content (message text)
├── message_hash (SHA-256)
├── embedding (1536-dimensional vector, pickled)
└── posted_at (timestamp)
```

**History management:**
- Stores last 365 days
- Auto-deletes messages older than 365 days
- One message per day maximum

### Backup

```bash
# Manual backup
cp data/motd.db data/motd.db.backup-$(date +%Y%m%d)

# With Docker
docker cp zenon-motd-bot:/app/data/motd.db ./backup.db

# Automated backup script
#!/bin/bash
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR
cp data/motd.db "$BACKUP_DIR/motd-$(date +%Y%m%d-%H%M%S).db"
find $BACKUP_DIR -name "motd-*.db" -mtime +30 -delete
```

### Restore

```bash
# Stop bot
docker-compose down

# Restore backup
cp backups/motd-20250122.db data/motd.db

# Start bot
docker-compose up -d
```

### Git Protection

**Files NOT committed to git:**
- `.env` - API keys and secrets
- `*.db` - Database files
- `venv/` - Virtual environment
- `__pycache__/` - Compiled Python

**Files committed:**
- `data/kaine_personality.md` - Personality config
- `data/mrkainez_posts.json` - Historical posts
- All Python code
- Docker files
- This README

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Bot Not Posting

**Check 1: DRY_RUN mode**
```bash
# Ensure DRY_RUN=false in .env
grep DRY_RUN .env
```

**Check 2: Bot is admin in channel**
- Go to channel settings
- Check bot has "Post Messages" permission

**Check 3: Channel ID correct**
```bash
# View configured channel
docker-compose run --rm motd-bot python -c "from config import Config; print(Config.TELEGRAM_CHANNEL_ID)"
```

### Messages Too Similar

**Symptom:** Frequent "Message too similar" warnings

**Solutions:**
```env
# Option 1: Relax threshold
SIMILARITY_THRESHOLD=0.87

# Option 2: Increase attempts
MAX_GENERATION_ATTEMPTS=7

# Option 3: Reduce history window
SIMILARITY_CHECK_DAYS=60
```

### OpenAI Errors

**Check 1: Valid API key**
```bash
# Test API key
docker-compose run --rm motd-bot python -c "
from openai import OpenAI
from config import Config
client = OpenAI(api_key=Config.OPENAI_API_KEY)
print('✅ API key valid')
"
```

**Check 2: Credits remaining**
- Visit: https://platform.openai.com/account/usage
- Ensure you have available credits

**Check 3: API status**
- Check: https://status.openai.com/

### Database Issues

```bash
# Check database exists
ls -lh data/motd.db

# View message count
docker-compose run --rm motd-bot python -c "
from database import MessageDatabase
db = MessageDatabase()
print(f'Messages: {db.get_message_count()}')
"

# Reset database (⚠️ deletes history)
docker-compose down
rm data/motd.db
docker-compose up -d
```

### Python 3.14 Compatibility

If using Python 3.14, you may see Pydantic warnings:

```
UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14
```

**This is harmless** and can be ignored. Bot works correctly.

To eliminate warning, use Python 3.11-3.13:
```bash
pyenv install 3.13.0
pyenv local 3.13.0
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Common Error Messages

**"There is no current event loop"**
- Fixed in current version
- Update: `git pull && docker-compose up -d --build`

**"ModuleNotFoundError: No module named 'dotenv'"**
- Virtual environment not activated or dependencies not installed
- Fix: `source venv/bin/activate && pip install -r requirements.txt`

**"Configuration errors: OPENAI_API_KEY is required"**
- Missing or incorrect `.env` file
- Fix: `cp .env.example .env` and edit with your keys

---

## Project Structure

```
motd-bot/
├── data/
│   ├── kaine_personality.md    # Personality & voice guidelines
│   ├── mrkainez_posts.json     # 882 historical Telegram posts
│   └── motd.db                 # Message database (gitignored)
├── venv/                       # Virtual environment (gitignored)
├── motd_bot.py                 # Main bot application
├── message_generator.py        # OpenAI integration & uniqueness
├── database.py                 # SQLite database management
├── config.py                   # Configuration from .env
├── test_motd.py               # Testing suite
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker service configuration
├── .env                        # Your configuration (gitignored)
├── .env.example               # Configuration template
├── .gitignore                 # Git exclusions
├── .dockerignore              # Docker build exclusions
└── README.md                   # This file
```

---

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | - | OpenAI API key for GPT-4 |
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | - | Bot token from @BotFather |
| `TELEGRAM_CHANNEL_ID` | ✅ Yes | - | Channel username or chat ID |
| `DAILY_POST_HOUR` | No | 5 | Hour to post (0-23, 24-hour) |
| `DAILY_POST_MINUTE` | No | 0 | Minute to post (0-59) |
| `TIMEZONE` | No | America/Chicago | Timezone (auto-handles DST) |
| `DRY_RUN` | No | false | Test mode (no actual posting) |
| `DATABASE_PATH` | No | motd.db | Database file path |
| `SIMILARITY_THRESHOLD` | No | 0.85 | Uniqueness threshold (0-1) |
| `MAX_GENERATION_ATTEMPTS` | No | 5 | Attempts before using best |
| `SIMILARITY_CHECK_DAYS` | No | 90 | Days of history to check |

### Docker Commands Reference

```bash
# Build & Start
docker-compose up -d                    # Start in background
docker-compose up                        # Start with logs
docker-compose up -d --build            # Rebuild and start

# Manage
docker-compose restart                   # Restart bot
docker-compose stop                      # Stop bot
docker-compose down                      # Stop and remove
docker-compose ps                        # Check status

# Logs
docker-compose logs -f                   # Follow logs
docker-compose logs --tail=100          # Last 100 lines
docker-compose logs | grep ERROR        # Show errors only

# Test
docker-compose run --rm motd-bot python test_motd.py all

# Execute Commands
docker-compose exec motd-bot /bin/bash  # Enter container
docker-compose exec motd-bot python -c "..."  # Run Python
```

---

## Credits

Built for the Zenon Network community.

**Powered by:**
- OpenAI GPT-4 for message generation
- OpenAI embeddings for semantic similarity
- python-telegram-bot for Telegram integration
- APScheduler for daily scheduling
- SQLite for message storage

**Special thanks to:**
- Mr. Kaine (@mrkainez) for the inspiration
- All Zenon developers, researchers, community managers, architects, and shitposters who build in silence

---

## License

Open source. Use responsibly and respect the Zenon Network community.

---

## Support

**Issues:** Report at your repository's issues page

**Questions:**
- Check this README first
- Review logs: `docker-compose logs`
- Run tests: `python test_motd.py all`

**Common solutions:**
- Restart: `docker-compose restart`
- Rebuild: `docker-compose up -d --build`
- Reset: `docker-compose down && rm data/motd.db && docker-compose up -d`
