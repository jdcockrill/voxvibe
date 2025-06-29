"""History storage for VoxVibe transcriptions using SQLite."""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class HistoryEntry:
    """Represents a single transcription history entry."""
    
    def __init__(self, id: int, text: str, timestamp: datetime):
        self.id = id
        self.text = text
        self.timestamp = timestamp
    
    def __repr__(self):
        return f"HistoryEntry(id={self.id}, text='{self.text[:30]}...', timestamp={self.timestamp})"


class HistoryStorage:
    """Manages transcription history storage with SQLite."""
    
    def __init__(self, db_path: str, max_entries: int = 20):
        self.db_path = Path(db_path).expanduser()
        self.max_entries = max_entries
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database and create tables if needed."""
        try:
            # Create parent directories if they don't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS transcriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON transcriptions(timestamp DESC)
                """)
                conn.commit()
            
            logger.info(f"History database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize history database: {e}")
            raise
    
    def save_transcription(self, text: str) -> bool:
        """
        Save a transcription to history.
        
        Args:
            text: The transcription text to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not text or not text.strip():
            logger.warning("Attempted to save empty transcription")
            return False
        
        try:
            timestamp = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                # Insert new transcription
                conn.execute(
                    "INSERT INTO transcriptions (text, timestamp) VALUES (?, ?)",
                    (text.strip(), timestamp)
                )
                
                # Trim to max entries if needed
                self._trim_entries(conn)
                
                conn.commit()
            
            logger.info(f"Saved transcription to history: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save transcription to history: {e}")
            return False
    
    def get_recent(self, limit: int = 3) -> List[HistoryEntry]:
        """
        Get the most recent transcriptions.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of HistoryEntry objects, newest first
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id, text, timestamp FROM transcriptions "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                
                entries = []
                for row in cursor.fetchall():
                    entry = HistoryEntry(
                        id=row[0],
                        text=row[1],
                        timestamp=datetime.fromisoformat(row[2])
                    )
                    entries.append(entry)
                
                return entries
                
        except Exception as e:
            logger.error(f"Failed to get recent transcriptions: {e}")
            return []
    
    
    
    
    def _trim_entries(self, conn: sqlite3.Connection):
        """Trim entries to max_entries limit, keeping the most recent."""
        try:
            # Count current entries
            cursor = conn.execute("SELECT COUNT(*) FROM transcriptions")
            count = cursor.fetchone()[0]
            
            if count > self.max_entries:
                # Delete oldest entries beyond the limit
                entries_to_delete = count - self.max_entries
                conn.execute(
                    "DELETE FROM transcriptions WHERE id IN ("
                    "SELECT id FROM transcriptions ORDER BY timestamp ASC LIMIT ?"
                    ")",
                    (entries_to_delete,)
                )
                logger.info(f"Trimmed {entries_to_delete} old entries from history")
                
        except Exception as e:
            logger.error(f"Failed to trim history entries: {e}")