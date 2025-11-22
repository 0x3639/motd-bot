"""Database management for message history."""
import sqlite3
import hashlib
import pickle
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from config import Config


class MessageDatabase:
    """Manages message history in SQLite database."""

    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        self.db_path = db_path or Config.DATABASE_PATH
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Connect to database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                content TEXT NOT NULL,
                message_hash TEXT NOT NULL,
                embedding BLOB,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date)
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_date ON messages(date)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hash ON messages(message_hash)
        ''')
        self.conn.commit()

    def _hash_content(self, content: str) -> str:
        """Generate hash of message content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def save_message(self, date: str, content: str, embedding: List[float] = None) -> bool:
        """Save a message to database with optional embedding."""
        try:
            cursor = self.conn.cursor()
            message_hash = self._hash_content(content)

            # Serialize embedding if provided
            embedding_blob = pickle.dumps(embedding) if embedding else None

            cursor.execute(
                'INSERT OR REPLACE INTO messages (date, content, message_hash, embedding) VALUES (?, ?, ?, ?)',
                (date, content, message_hash, embedding_blob)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error saving message: {e}")
            return False

    def get_message_by_date(self, date: str) -> Optional[str]:
        """Get message for a specific date."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT content FROM messages WHERE date = ?', (date,))
        row = cursor.fetchone()
        return row['content'] if row else None

    def get_today_message(self) -> Optional[str]:
        """Get today's message if it exists."""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.get_message_by_date(today)

    def get_recent_messages(self, days: int = None) -> List[str]:
        """Get messages from the last N days."""
        days = days or Config.HISTORY_DAYS
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT content FROM messages WHERE date >= ? ORDER BY date DESC',
            (cutoff_date,)
        )
        return [row['content'] for row in cursor.fetchall()]

    def get_recent_embeddings(self, days: int = None) -> List[Tuple[str, List[float]]]:
        """Get messages with embeddings from the last N days."""
        days = days or Config.HISTORY_DAYS
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT content, embedding FROM messages WHERE date >= ? AND embedding IS NOT NULL ORDER BY date DESC',
            (cutoff_date,)
        )
        results = []
        for row in cursor.fetchall():
            content = row['content']
            embedding = pickle.loads(row['embedding']) if row['embedding'] else None
            if embedding:
                results.append((content, embedding))
        return results

    def is_duplicate(self, content: str) -> bool:
        """Check if content is too similar to existing messages."""
        message_hash = self._hash_content(content)
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM messages WHERE message_hash = ?', (message_hash,))
        result = cursor.fetchone()
        return result['count'] > 0

    def cleanup_old_messages(self, days: int = None):
        """Delete messages older than specified days."""
        days = days or Config.HISTORY_DAYS
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM messages WHERE date < ?', (cutoff_date,))
        deleted = cursor.rowcount
        self.conn.commit()
        return deleted

    def get_message_count(self) -> int:
        """Get total number of messages in database."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM messages')
        result = cursor.fetchone()
        return result['count']

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
