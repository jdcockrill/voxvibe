"""Transcription history management for VoxVibe.

Provides SQLite-based storage for recent transcriptions with safety net functionality.
"""
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from dataclasses import dataclass


@dataclass
class HistoryEntry:
    id: int
    text: str
    timestamp: datetime
    duration_ms: int = 0
    mode: str = "unknown"


class TranscriptionHistory:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            # Default to ~/.cache/voxvibe/history.sqlite
            cache_dir = Path.home() / ".cache" / "voxvibe"
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = cache_dir / "history.sqlite"
        
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database and create tables if needed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS transcriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        duration_ms INTEGER DEFAULT 0,
                        mode TEXT DEFAULT 'unknown'
                    )
                """)
                
                # Create index for faster timestamp queries
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON transcriptions(timestamp DESC)
                """)
                
                conn.commit()
                print(f"📚 History database initialized: {self.db_path}")
                
        except Exception as e:
            print(f"⚠️ Failed to initialize history database: {e}")
    
    def add_entry(self, text: str, duration_ms: int = 0, mode: str = "unknown") -> int:
        """Add a new transcription to history
        
        Args:
            text: The transcribed text
            duration_ms: Recording duration in milliseconds
            mode: Recording mode (hold_to_talk, hands_free, etc.)
            
        Returns:
            The ID of the inserted entry
        """
        if not text.strip():
            return -1
            
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        INSERT INTO transcriptions (text, duration_ms, mode)
                        VALUES (?, ?, ?)
                    """, (text.strip(), duration_ms, mode))
                    
                    entry_id = cursor.lastrowid
                    conn.commit()
                    
                    # Clean up old entries (keep last 50)
                    self._cleanup_old_entries(conn)
                    
                    print(f"📝 Added history entry #{entry_id}: {text[:50]}...")
                    return entry_id
                    
            except Exception as e:
                print(f"⚠️ Failed to add history entry: {e}")
                return -1
    
    def _cleanup_old_entries(self, conn: sqlite3.Connection):
        """Remove old entries, keeping only the most recent 50"""
        try:
            conn.execute("""
                DELETE FROM transcriptions 
                WHERE id NOT IN (
                    SELECT id FROM transcriptions 
                    ORDER BY timestamp DESC 
                    LIMIT 50
                )
            """)
        except Exception as e:
            print(f"⚠️ Failed to cleanup old entries: {e}")
    
    def get_recent(self, limit: int = 10) -> List[HistoryEntry]:
        """Get recent transcription entries
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of HistoryEntry objects, most recent first
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute("""
                        SELECT id, text, timestamp, duration_ms, mode
                        FROM transcriptions 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (limit,))
                    
                    entries = []
                    for row in cursor:
                        entries.append(HistoryEntry(
                            id=row['id'],
                            text=row['text'],
                            timestamp=datetime.fromisoformat(row['timestamp']),
                            duration_ms=row['duration_ms'],
                            mode=row['mode']
                        ))
                    
                    return entries
                    
            except Exception as e:
                print(f"⚠️ Failed to get recent entries: {e}")
                return []
    
    def get_last_entry(self) -> Optional[HistoryEntry]:
        """Get the most recent transcription entry"""
        entries = self.get_recent(limit=1)
        return entries[0] if entries else None
    
    def get_entry_by_id(self, entry_id: int) -> Optional[HistoryEntry]:
        """Get a specific entry by ID"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute("""
                        SELECT id, text, timestamp, duration_ms, mode
                        FROM transcriptions 
                        WHERE id = ?
                    """, (entry_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        return HistoryEntry(
                            id=row['id'],
                            text=row['text'],
                            timestamp=datetime.fromisoformat(row['timestamp']),
                            duration_ms=row['duration_ms'],
                            mode=row['mode']
                        )
                    
            except Exception as e:
                print(f"⚠️ Failed to get entry {entry_id}: {e}")
        
        return None
    
    def search_entries(self, query: str, limit: int = 20) -> List[HistoryEntry]:
        """Search transcription entries by text content
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching HistoryEntry objects
        """
        if not query.strip():
            return []
            
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute("""
                        SELECT id, text, timestamp, duration_ms, mode
                        FROM transcriptions 
                        WHERE text LIKE ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (f"%{query.strip()}%", limit))
                    
                    entries = []
                    for row in cursor:
                        entries.append(HistoryEntry(
                            id=row['id'],
                            text=row['text'],
                            timestamp=datetime.fromisoformat(row['timestamp']),
                            duration_ms=row['duration_ms'],
                            mode=row['mode']
                        ))
                    
                    return entries
                    
            except Exception as e:
                print(f"⚠️ Failed to search entries: {e}")
                return []
    
    def delete_entry(self, entry_id: int) -> bool:
        """Delete a specific entry by ID"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        DELETE FROM transcriptions WHERE id = ?
                    """, (entry_id,))
                    
                    deleted = cursor.rowcount > 0
                    conn.commit()
                    
                    if deleted:
                        print(f"🗑️ Deleted history entry #{entry_id}")
                    
                    return deleted
                    
            except Exception as e:
                print(f"⚠️ Failed to delete entry {entry_id}: {e}")
                return False
    
    def clear_all(self) -> bool:
        """Clear all history entries"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM transcriptions")
                    conn.commit()
                    print("🗑️ Cleared all history entries")
                    return True
                    
            except Exception as e:
                print(f"⚠️ Failed to clear history: {e}")
                return False
    
    def get_stats(self) -> dict:
        """Get statistics about the history database"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_entries,
                            SUM(duration_ms) as total_duration_ms,
                            AVG(duration_ms) as avg_duration_ms,
                            MIN(timestamp) as earliest,
                            MAX(timestamp) as latest
                        FROM transcriptions
                    """)
                    
                    row = cursor.fetchone()
                    if row:
                        return {
                            'total_entries': row[0],
                            'total_duration_ms': row[1] or 0,
                            'avg_duration_ms': row[2] or 0,
                            'earliest': row[3],
                            'latest': row[4]
                        }
                    
            except Exception as e:
                print(f"⚠️ Failed to get stats: {e}")
        
        return {
            'total_entries': 0,
            'total_duration_ms': 0,
            'avg_duration_ms': 0,
            'earliest': None,
            'latest': None
        } 