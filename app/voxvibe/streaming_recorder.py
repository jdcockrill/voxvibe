import asyncio
import logging
import queue
from typing import Optional

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from .audio_recorder import AudioRecorder
from .event_bus import Events, event_bus
from .transcriber import StreamingTranscriber

logger = logging.getLogger(__name__)


class StreamingRecordingThread(QThread):
    """
    Enhanced recording thread that supports streaming transcription.
    
    This thread handles both streaming transcription (emitting partial/final events)
    and backward compatibility (providing final result via signal).
    """
    
    recording_finished = pyqtSignal(object)  # For backward compatibility
    
    def __init__(self):
        super().__init__()
        self.recorder = AudioRecorder(chunk_duration_ms=320)  # 320ms chunks as required
        self.transcriber = StreamingTranscriber(model_size="base.en")
        self.should_stop = False
        self.chunk_queue = queue.Queue()
        self.final_text = ""
        self.partial_texts = []
        
        # Set up event callbacks
        self.transcriber.add_event_callback(self._on_transcript_event)
    
    def _on_transcript_event(self, text: str, is_partial: bool):
        """Handle transcript events from the transcriber"""
        if is_partial:
            self.partial_texts.append(text)
            event_bus.emit(Events.TRANSCRIPT_PARTIAL, {"text": text, "is_partial": True})
            logger.debug(f"Partial transcript: {text}")
        else:
            self.final_text = text
            event_bus.emit(Events.TRANSCRIPT_FINAL, {"text": text, "is_partial": False})
            logger.info(f"Final transcript: {text}")
    
    def _on_audio_chunk(self, chunk: np.ndarray):
        """Callback for audio chunks from the recorder"""
        try:
            self.chunk_queue.put(chunk, timeout=0.1)
        except queue.Full:
            logger.warning("Audio chunk queue full, dropping chunk")
    
    async def _async_transcription_loop(self):
        """Async loop that processes audio chunks through the transcriber"""
        try:
            while not self.should_stop or not self.chunk_queue.empty():
                try:
                    # Get chunk with timeout to allow checking should_stop
                    chunk = self.chunk_queue.get(timeout=0.1)
                    
                    # Create async iterator for the single chunk
                    async def chunk_iterator():
                        yield chunk
                    
                    # Process chunk through streaming transcriber
                    async for text, is_partial in self.transcriber.stream_transcribe(chunk_iterator()):
                        # Events are already emitted by the transcriber callback
                        pass
                        
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.exception(f"Error processing audio chunk: {e}")
                    
        except Exception as e:
            logger.exception(f"Error in transcription loop: {e}")
    
    def run(self):
        """Main thread execution"""
        try:
            logger.info("Starting streaming recording")
            event_bus.emit(Events.RECORDING_STARTED)
            
            # Start recording with chunk callback
            self.recorder.start_recording(chunk_callback=self._on_audio_chunk)
            
            # Start async transcription in a separate thread context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the transcription loop
            transcription_task = loop.create_task(self._async_transcription_loop())
            
            # Wait for stop signal
            while not self.should_stop:
                self.msleep(100)
            
            logger.info("Stopping recording")
            event_bus.emit(Events.RECORDING_STOPPED)
            
            # Stop recording
            audio_data = self.recorder.stop_recording()
            
            # Wait for transcription to complete
            transcription_task.cancel()
            try:
                loop.run_until_complete(transcription_task)
            except asyncio.CancelledError:
                pass
            
            # If we don't have a final result from streaming, fall back to batch
            if not self.final_text and audio_data is not None:
                logger.info("No streaming result, falling back to batch transcription")
                event_bus.emit(Events.TRANSCRIPTION_STARTED)
                
                self.final_text = self.transcriber.transcribe_batch(audio_data)
                
                if self.final_text:
                    event_bus.emit(Events.TRANSCRIPT_FINAL, {"text": self.final_text, "is_partial": False})
                
                event_bus.emit(Events.TRANSCRIPTION_COMPLETED)
            
            # Emit result for backward compatibility
            self.recording_finished.emit(self.final_text)
            
            loop.close()
            
        except Exception as e:
            logger.exception(f"Error in streaming recording thread: {e}")
            event_bus.emit(Events.ERROR, {"error": str(e)})
            self.recording_finished.emit(None)
    
    def stop_recording(self):
        """Stop the recording"""
        self.should_stop = True


# Backward compatibility alias
RecordingThread = StreamingRecordingThread