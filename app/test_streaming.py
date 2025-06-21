#!/usr/bin/env python3
"""
Basic test script to validate the streaming transcription implementation.
This script tests imports and basic functionality without requiring whisperflow.
"""

import logging
import sys
import traceback
from pathlib import Path

# Add the voxvibe package to the path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all our new modules can be imported"""
    try:
        from voxvibe.event_bus import EventBus, Events, event_bus
        logger.info("✅ event_bus imported successfully")
        
        from voxvibe.audio_recorder import AudioRecorder
        logger.info("✅ audio_recorder imported successfully")
        
        from voxvibe.transcriber import StreamingTranscriber, Transcriber
        logger.info("✅ transcriber imported successfully")
        
        from voxvibe.streaming_recorder import StreamingRecordingThread
        logger.info("✅ streaming_recorder imported successfully")
        
        return True
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False


def test_event_bus():
    """Test the event bus functionality"""
    try:
        from voxvibe.event_bus import EventBus, Events
        
        bus = EventBus()
        received_events = []
        
        def test_callback(data):
            received_events.append(data)
        
        # Test subscription and emission
        bus.subscribe(Events.TRANSCRIPT_PARTIAL, test_callback)
        bus.emit(Events.TRANSCRIPT_PARTIAL, {"text": "test", "is_partial": True})
        
        if len(received_events) == 1 and received_events[0]["text"] == "test":
            logger.info("✅ Event bus working correctly")
            return True
        else:
            logger.error("❌ Event bus test failed")
            return False
    except Exception as e:
        logger.error(f"❌ Event bus test failed: {e}")
        traceback.print_exc()
        return False


def test_audio_recorder():
    """Test the enhanced audio recorder"""
    try:
        from voxvibe.audio_recorder import AudioRecorder
        
        recorder = AudioRecorder(chunk_duration_ms=320)
        
        # Test that we can create the recorder
        assert recorder.chunk_size == int(16000 * 320 / 1000), "Chunk size calculation incorrect"
        assert recorder.chunk_callback is None, "Chunk callback should be None initially"
        
        logger.info("✅ AudioRecorder basic functionality working")
        return True
    except Exception as e:
        logger.error(f"❌ AudioRecorder test failed: {e}")
        traceback.print_exc()
        return False


def test_transcriber():
    """Test the transcriber (will handle whisperflow being unavailable)"""
    try:
        from voxvibe.transcriber import StreamingTranscriber, Transcriber, WHISPERFLOW_AVAILABLE
        
        if not WHISPERFLOW_AVAILABLE:
            logger.info("ℹ️ whisperflow not available - testing fallback behavior")
        
        transcriber = StreamingTranscriber()
        
        # Test event callback system
        received_callbacks = []
        
        def test_callback(text, is_partial):
            received_callbacks.append((text, is_partial))
        
        transcriber.add_event_callback(test_callback)
        transcriber._emit_event("test", True)
        
        if len(received_callbacks) == 1 and received_callbacks[0] == ("test", True):
            logger.info("✅ Transcriber event system working")
        else:
            logger.error("❌ Transcriber event system failed")
            return False
        
        # Test backward compatibility wrapper
        compat_transcriber = Transcriber()
        if hasattr(compat_transcriber, 'transcribe'):
            logger.info("✅ Backward compatibility wrapper working")
        else:
            logger.error("❌ Backward compatibility wrapper failed")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Transcriber test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    logger.info("Starting streaming transcription validation tests...")
    
    tests = [
        ("Imports", test_imports),
        ("Event Bus", test_event_bus),
        ("Audio Recorder", test_audio_recorder),
        ("Transcriber", test_transcriber),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} test PASSED")
            else:
                failed += 1
                logger.error(f"❌ {test_name} test FAILED")
        except Exception as e:
            failed += 1
            logger.error(f"❌ {test_name} test FAILED with exception: {e}")
    
    logger.info(f"\n--- Test Results ---")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Streaming implementation structure is valid.")
        return 0
    else:
        logger.error("⚠️ Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())