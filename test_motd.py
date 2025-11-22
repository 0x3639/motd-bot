"""
Local testing script for MOTD bot.
Test message generation without posting to Telegram.
"""
import asyncio
import sys
from datetime import datetime
from config import Config
from database import MessageDatabase
from message_generator import MessageGenerator


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60 + "\n")


def test_config():
    """Test configuration loading."""
    print_header("Testing Configuration")

    print(f"OpenAI API Key: {'Set' if Config.OPENAI_API_KEY else 'NOT SET'}")
    print(f"Telegram Bot Token: {'Set' if Config.TELEGRAM_BOT_TOKEN else 'NOT SET'}")
    print(f"Telegram Channel ID: {Config.TELEGRAM_CHANNEL_ID or 'NOT SET'}")
    print(f"Dry Run Mode: {Config.DRY_RUN}")
    print(f"Database Path: {Config.DATABASE_PATH}")
    print(f"Daily Post Time: {Config.DAILY_POST_HOUR:02d}:{Config.DAILY_POST_MINUTE:02d} {Config.TIMEZONE}")
    print(f"History Days: {Config.HISTORY_DAYS}")

    try:
        Config.validate()
        print("\n✅ Configuration is valid")
        return True
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        return False


def test_database():
    """Test database operations."""
    print_header("Testing Database")

    try:
        db = MessageDatabase()
        count = db.get_message_count()
        print(f"Total messages in database: {count}")

        # Test today's message
        today_msg = db.get_today_message()
        if today_msg:
            print(f"\n✅ Found existing message for today:")
            print(f"{today_msg[:200]}...")
        else:
            print("\nℹ️  No message exists for today yet")

        # Test recent messages
        recent = db.get_recent_messages(days=7)
        print(f"\nMessages in last 7 days: {len(recent)}")

        db.close()
        print("\n✅ Database tests passed")
        return True
    except Exception as e:
        print(f"\n❌ Database error: {e}")
        return False


def test_message_generation():
    """Test message generation."""
    print_header("Testing Message Generation")

    try:
        # Initialize components
        db = MessageDatabase()
        generator = MessageGenerator()

        # Get recent messages for context
        recent_messages = db.get_recent_messages(days=30)
        print(f"Using {len(recent_messages)} recent messages for context")

        # Get recent embeddings for similarity checking
        from config import Config
        recent_embeddings = db.get_recent_embeddings(days=Config.SIMILARITY_CHECK_DAYS)
        print(f"Retrieved {len(recent_embeddings)} embeddings for similarity checking")
        print(f"Similarity threshold: {Config.SIMILARITY_THRESHOLD:.2%}")
        print(f"Max attempts: {Config.MAX_GENERATION_ATTEMPTS}\n")

        # Generate message
        print("Generating new message (this may take a few seconds)...\n")
        message, embedding = generator.generate_with_retry(
            previous_messages=recent_messages,
            recent_embeddings=recent_embeddings,
            max_attempts=Config.MAX_GENERATION_ATTEMPTS,
            similarity_threshold=Config.SIMILARITY_THRESHOLD
        )

        if message:
            print("✅ Message generated successfully!\n")
            print("-" * 60)
            print(message)
            print("-" * 60)

            # Validate message
            is_valid = generator.validate_message(message)
            print(f"\nValidation: {'✅ Passed' if is_valid else '❌ Failed'}")
            print(f"Length: {len(message)} characters")

            # Check for duplicates
            is_duplicate = db.is_duplicate(message)
            print(f"Duplicate check: {'⚠️  Duplicate found' if is_duplicate else '✅ Unique'}")

            print("\nℹ️  Note: Message NOT saved to database (this is a read-only test)")
            print("   To save a message, run: python test_motd.py save")

            db.close()
            return True
        else:
            print("❌ Failed to generate message")
            db.close()
            return False

    except Exception as e:
        print(f"\n❌ Generation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_save_message():
    """Test saving a message to database."""
    print_header("Testing Message Save")

    try:
        db = MessageDatabase()
        generator = MessageGenerator()

        # Check for existing message
        today = datetime.now().strftime('%Y-%m-%d')
        existing = db.get_message_by_date(today)

        if existing:
            print(f"ℹ️  Message already exists for {today}")
            print("Do you want to generate a new one? (y/n): ", end="")
            response = input().strip().lower()
            if response != 'y':
                print("Skipping message generation")
                db.close()
                return True

        # Generate and save
        from config import Config
        recent_messages = db.get_recent_messages()
        recent_embeddings = db.get_recent_embeddings(days=Config.SIMILARITY_CHECK_DAYS)
        print(f"\nGenerating message (checking against {len(recent_embeddings)} recent embeddings)...")
        message, embedding = generator.generate_with_retry(
            previous_messages=recent_messages,
            recent_embeddings=recent_embeddings,
            max_attempts=Config.MAX_GENERATION_ATTEMPTS,
            similarity_threshold=Config.SIMILARITY_THRESHOLD
        )

        if message:
            print("\n✅ Message generated")
            saved = db.save_message(today, message, embedding)

            if saved:
                print(f"✅ Message saved to database for {today}")
                print("\nSaved message:")
                print("-" * 60)
                print(message)
                print("-" * 60)
            else:
                print("❌ Failed to save message")

            db.close()
            return saved
        else:
            print("❌ Failed to generate message")
            db.close()
            return False

    except Exception as e:
        print(f"\n❌ Save error: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "🚀 " * 20)
    print("ZENON NETWORK MOTD BOT - TEST SUITE")
    print("🚀 " * 20)

    results = {
        'Configuration': test_config(),
        'Database': test_database(),
    }

    # Only run generation tests if basic tests pass
    if all(results.values()):
        results['Message Generation'] = test_message_generation()

    # Summary
    print_header("Test Summary")
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    return all_passed


def main():
    """Main test entry point."""
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()

        if test_type == 'config':
            test_config()
        elif test_type == 'database':
            test_database()
        elif test_type == 'generate':
            test_message_generation()
        elif test_type == 'save':
            test_save_message()
        elif test_type == 'all':
            run_all_tests()
        else:
            print(f"Unknown test type: {test_type}")
            print("\nAvailable tests:")
            print("  python test_motd.py config    - Test configuration")
            print("  python test_motd.py database  - Test database")
            print("  python test_motd.py generate  - Test message generation")
            print("  python test_motd.py save      - Generate and save today's message")
            print("  python test_motd.py all       - Run all tests")
    else:
        # Default: run all tests
        run_all_tests()


if __name__ == '__main__':
    main()
