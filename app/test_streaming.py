#!/usr/bin/env python3
"""
Test script for VoxVibe streaming transcription implementation.

This script validates the whisper_streaming integration and event system.
"""
import logging
import time
import sys
import threading
from pathlib import Path

# Add the voxvibe package to the path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from voxvibe.event_bus import (
    get_event_bus,
    EventType,
    TranscriptEvent,
    emit_partial_transcript,
    emit_final_transcript
)
from voxvibe.transcriber import StreamingTranscriber
from voxvibe.audio_recorder import AudioRecorder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StreamingTestValidator:
    """Test validator for streaming transcription"""
    
    def __init__(self):
        self.received_events = []
        self.partial_transcripts = []
        self.final_transcripts = []
        
        # Subscribe to events
        event_bus = get_event_bus()
        event_bus.subscribe(EventType.PARTIAL_TRANSCRIPT, self._on_partial)
        event_bus.subscribe(EventType.FINAL_TRANSCRIPT, self._on_final)
        event_bus.subscribe(EventType.TRANSCRIPTION_STARTED, self._on_started)
        event_bus.subscribe(EventType.TRANSCRIPTION_ENDED, self._on_ended)
        event_bus.subscribe(EventType.TRANSCRIPTION_ERROR, self._on_error)
    
    def _on_partial(self, event: TranscriptEvent):
        logger.info(f"📝 PARTIAL: {event.text}")
        self.partial_transcripts.append(event.text)
        self.received_events.append(('partial', event.text))
    
    def _on_final(self, event: TranscriptEvent):
        logger.info(f"✅ FINAL: {event.text}")
        self.final_transcripts.append(event.text)
        self.received_events.append(('final', event.text))
    
    def _on_started(self, event: TranscriptEvent):
        logger.info("🎬 Transcription started")
        self.received_events.append(('started', ''))
    
    def _on_ended(self, event: TranscriptEvent):
        logger.info("🎬 Transcription ended")
        self.received_events.append(('ended', ''))
    
    def _on_error(self, event: TranscriptEvent):
        logger.error(f"❌ Error: {event.text}")
        self.received_events.append(('error', event.text))
    
    def print_summary(self):
        logger.info("\n" + "="*50)
        logger.info("📊 STREAMING TEST SUMMARY")
        logger.info("="*50)
        logger.info(f"Total events received: {len(self.received_events)}")
        logger.info(f"Partial transcripts: {len(self.partial_transcripts)}")
        logger.info(f"Final transcripts: {len(self.final_transcripts)}")
        
        if self.partial_transcripts:
            logger.info("\nPartial transcripts:")
            for i, text in enumerate(self.partial_transcripts):
                logger.info(f"  {i+1}. {text}")
        
        if self.final_transcripts:
            logger.info("\nFinal transcripts:")
            for i, text in enumerate(self.final_transcripts):
                logger.info(f"  {i+1}. {text}")
        
        logger.info("\nEvent timeline:")
        for i, (event_type, text) in enumerate(self.received_events):
            logger.info(f"  {i+1}. {event_type}: {text}")


def test_event_bus():
    """Test the event bus system"""
    logger.info("🧪 Testing event bus system...")
    
    validator = StreamingTestValidator()
    
    # Emit test events
    emit_partial_transcript("Hello", timestamp=0.5)
    emit_partial_transcript("Hello world", timestamp=1.0)
    emit_final_transcript("Hello world", timestamp=1.5)
    emit_partial_transcript("How are", timestamp=2.0)
    emit_partial_transcript("How are you", timestamp=2.5)
    emit_final_transcript("How are you", timestamp=3.0)
    
    time.sleep(0.1)  # Allow events to process
    
    # Validate results
    assert len(validator.partial_transcripts) == 4, f"Expected 4 partial transcripts, got {len(validator.partial_transcripts)}"
    assert len(validator.final_transcripts) == 2, f"Expected 2 final transcripts, got {len(validator.final_transcripts)}"
    
    logger.info("✅ Event bus test passed!")
    return True


def test_transcriber_initialization():
    """Test transcriber initialization and fallback behavior"""
    logger.info("🧪 Testing transcriber initialization...")
    
    try:
        transcriber = StreamingTranscriber(model_size="base")
        logger.info(f"✅ Transcriber initialized successfully")
        
        # Test method availability
        assert hasattr(transcriber, 'start_streaming'), "Missing start_streaming method"
        assert hasattr(transcriber, 'stop_streaming'), "Missing stop_streaming method"
        assert hasattr(transcriber, 'process_audio_chunk'), "Missing process_audio_chunk method"
        assert hasattr(transcriber, 'transcribe_batch'), "Missing transcribe_batch method"
        
        logger.info("✅ All required methods are available")
        
        # Test that we can create audio chunks
        sample_audio = np.random.randn(5120).astype(np.float32) * 0.1  # 320ms at 16kHz
        
        # Test streaming mode
        transcriber.start_streaming()
        logger.info("✅ Streaming started successfully")
        
        # Process a few chunks (won't produce real transcripts with random noise)
        for i in range(3):
            transcriber.process_audio_chunk(sample_audio)
            time.sleep(0.1)
        
        final_text = transcriber.stop_streaming()
        logger.info(f"✅ Streaming stopped successfully. Final text: '{final_text}'")
        
        # Test batch mode fallback
        batch_result = transcriber.transcribe_batch(sample_audio)
        logger.info(f"✅ Batch transcription completed. Result: '{batch_result}'")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ Transcriber test failed: {e}")
        return False


def test_audio_recorder():
    """Test audio recorder streaming functionality"""
    logger.info("🧪 Testing audio recorder streaming...")
    
    try:
        recorder = AudioRecorder(chunk_duration=0.32)
        
        # Test chunk callback setup
        received_chunks = []
        
        def chunk_callback(audio_chunk):
            received_chunks.append(audio_chunk)
            logger.info(f"📼 Received audio chunk: {len(audio_chunk)} samples")
        
        recorder.set_chunk_callback(chunk_callback)
        
        # Test that devices are available
        devices = recorder.get_available_devices()
        logger.info(f"✅ Found {len(devices)} audio input devices")
        
        if devices:
            for device in devices[:3]:  # Show first 3 devices
                logger.info(f"  - {device['name']} ({device['id']})")
        
        logger.info("✅ Audio recorder test passed!")
        return True
        
    except Exception as e:
        logger.exception(f"❌ Audio recorder test failed: {e}")
        return False


def run_integration_test():
    """Run a comprehensive integration test"""
    logger.info("🧪 Running integration test...")
    
    validator = StreamingTestValidator()
    
    try:
        # Initialize components
        transcriber = StreamingTranscriber(model_size="base")
        recorder = AudioRecorder(chunk_duration=0.32)
        
        # Set up streaming
        recorder.set_chunk_callback(transcriber.process_audio_chunk)
        
        logger.info("✅ Integration components initialized")
        
        # Test with synthetic audio (silence)
        transcriber.start_streaming()
        
        # Generate some audio chunks (silence - won't transcribe but tests the pipeline)
        for i in range(5):
            # Create 320ms of silence
            silence = np.zeros(5120, dtype=np.float32)
            transcriber.process_audio_chunk(silence)
            time.sleep(0.1)
        
        final_result = transcriber.stop_streaming()
        
        logger.info(f"✅ Integration test completed. Final result: '{final_result}'")
        validator.print_summary()
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ Integration test failed: {e}")
        return False


def main():
    """Main test runner"""
    logger.info("🚀 Starting VoxVibe streaming transcription validation")
    logger.info("="*60)
    
    tests = [
        ("Event Bus", test_event_bus),
        ("Transcriber Initialization", test_transcriber_initialization), 
        ("Audio Recorder", test_audio_recorder),
        ("Integration Test", run_integration_test),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} test...")
        try:
            if test_func():
                logger.info(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} test FAILED")
                failed += 1
        except Exception as e:
            logger.exception(f"❌ {test_name} test FAILED with exception: {e}")
            failed += 1
    
    logger.info("\n" + "="*60)
    logger.info("📋 FINAL TEST RESULTS")
    logger.info("="*60)
    logger.info(f"✅ Tests passed: {passed}")
    logger.info(f"❌ Tests failed: {failed}")
    logger.info(f"📊 Success rate: {passed}/{passed+failed} ({100*passed/(passed+failed):.1f}%)")
    
    if failed == 0:
        logger.info("\n🎉 All tests passed! Streaming implementation is ready.")
        return 0
    else:
        logger.error(f"\n⚠️  {failed} test(s) failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())