"""History storage for VoxVibe transcriptions using SQLite.

This module provides a simple interface for storing and retrieving transcription
history in a local SQLite database at ~/.local/share/voxvibe/history.db.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from .config import get_config

logger = logging.getLogger(__name__)


class HistoryStorage:
    """Manages transcription history storage in SQLite database."""
    
    def __init__(self, max_entries: Optional[int] = None):
        """Initialize history storage.
        
        Args:
            max_entries: Maximum number of history entries to keep (uses config if None)
        """
        config = get_config()
        self.max_entries = max_entries if max_entries is not None else config.get_history_max_entries()
        self.db_path = self._get_db_path()
        self._init_database()
    
    def _get_db_path(self) -> Path:
        """Get the path to the history database file."""
        # Create ~/.local/share/voxvibe/ directory if it doesn't exist
        data_dir = Path.home() / ".local" / "share" / "voxvibe"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "history.db"
    
    def _init_database(self):
        """Initialize the SQLite database and create tables if needed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS transcriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text TEXT NOT NULL,
                        ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info(f"History database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize history database: {e}")
            raise
    
    def add_transcription(self, text: str) -> bool:
        """Add a new transcription to the history.
        
        Args:
            text: The transcribed text to store
            
        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            logger.warning("Empty transcription text, not adding to history")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Insert new transcription
                conn.execute(
                    'INSERT INTO transcriptions (text, ts) VALUES (?, ?)',
                    (text.strip(), datetime.now())
                )
                
                # Trim old entries if we exceed max_entries
                conn.execute('''
                    DELETE FROM transcriptions 
                    WHERE id NOT IN (
                        SELECT id FROM transcriptions 
                        ORDER BY ts DESC 
                        LIMIT ?
                    )
                ''', (self.max_entries,))
                
                conn.commit()
                logger.info(f"Added transcription to history (length: {len(text.strip())})")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to add transcription to history: {e}")
            return False
    
    def get_history(self, limit: Optional[int] = None) -> List[Tuple[int, str, datetime]]:
        """Get transcription history entries.
        
        Args:
            limit: Maximum number of entries to return (None for all)
            
        Returns:
            List of tuples (id, text, timestamp) ordered by newest first
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Configure datetime parsing
                conn.row_factory = sqlite3.Row
                
                if limit is not None:
                    cursor = conn.execute(
                        'SELECT id, text, ts FROM transcriptions ORDER BY ts DESC LIMIT ?',
                        (limit,)
                    )
                else:
                    cursor = conn.execute(
                        'SELECT id, text, ts FROM transcriptions ORDER BY ts DESC'
                    )
                
                rows = cursor.fetchall()
                
                # Convert to list of tuples with proper datetime objects
                history = []
                for row in rows:
                    # Parse datetime string from SQLite
                    dt = datetime.fromisoformat(row['ts'].replace(' ', 'T'))
                    history.append((row['id'], row['text'], dt))
                
                logger.info(f"Retrieved {len(history)} history entries")
                return history
                
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve history: {e}")
            return []
    
    def clear_history(self) -> bool:
        """Clear all transcription history.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM transcriptions')
                conn.commit()
                logger.info("Cleared all transcription history")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to clear history: {e}")
            return False
    
    def get_history_count(self) -> int:
        """Get the total number of history entries.
        
        Returns:
            Number of entries in history
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM transcriptions')
                count = cursor.fetchone()[0]
                return count
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get history count: {e}")
            return 0
    
    def set_max_entries(self, max_entries: int):
        """Set the maximum number of history entries and trim if necessary.
        
        Args:
            max_entries: New maximum number of entries
        """
        if max_entries <= 0:
            logger.warning("max_entries must be positive, ignoring")
            return
        
        self.max_entries = max_entries
        
        # Trim existing entries if needed
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    DELETE FROM transcriptions 
                    WHERE id NOT IN (
                        SELECT id FROM transcriptions 
                        ORDER BY ts DESC 
                        LIMIT ?
                    )
                ''', (self.max_entries,))
                conn.commit()
                logger.info(f"Set max_entries to {max_entries} and trimmed history")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to set max_entries: {e}")