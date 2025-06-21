#!/usr/bin/env python3
"""Test script for VoxVibe history functionality.

This script can be used to test the history storage and configuration system.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from voxvibe.history_storage import HistoryStorage
from voxvibe.config import get_config


def test_history_storage():
    """Test the history storage functionality."""
    print("Testing VoxVibe History Storage")
    print("=" * 40)
    
    # Test configuration
    config = get_config()
    print(f"History enabled: {config.get_history_enabled()}")
    print(f"Max entries: {config.get_history_max_entries()}")
    print(f"Retention days: {config.get_history_retention_days()}")
    print()
    
    # Test history storage
    storage = HistoryStorage()
    
    # Add some test transcriptions
    test_texts = [
        "This is a test transcription.",
        "Another test entry for the history.",
        "Testing the history functionality works correctly.",
        "Final test entry to verify storage."
    ]
    
    print("Adding test transcriptions...")
    for i, text in enumerate(test_texts, 1):
        success = storage.add_transcription(text)
        print(f"  {i}. Added: {success}")
    
    print()
    
    # Retrieve history
    print("Retrieving history...")
    history = storage.get_history()
    print(f"Found {len(history)} entries:")
    
    for i, (entry_id, text, timestamp) in enumerate(history, 1):
        print(f"  {i}. [{entry_id}] {timestamp.strftime('%Y-%m-%d %H:%M:%S')}: {text[:50]}...")
    
    print()
    
    # Test history count
    count = storage.get_history_count()
    print(f"Total history count: {count}")
    
    print()
    print("History test completed successfully!")


def clear_history():
    """Clear all history."""
    storage = HistoryStorage()
    success = storage.clear_history()
    print(f"History cleared: {success}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_history()
    else:
        test_history_storage()