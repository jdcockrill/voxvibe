import logging
import queue
import threading
from typing import Optional, Callable

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1, chunk_duration=0.32):
        """
        Initialize audio recorder with streaming support.
        
        Args:
            sample_rate: Audio sample rate (16000 for Whisper)
            channels: Number of audio channels (1 for mono)
            chunk_duration: Duration of each audio chunk in seconds (0.32 = 320ms)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        
        # Streaming callbacks
        self.chunk_callback = None
        self.is_streaming = False
        
        # Set default device to None to use system default
        sd.default.samplerate = sample_rate
        sd.default.channels = channels
        sd.default.dtype = np.float32
    
    def set_chunk_callback(self, callback: Callable[[np.ndarray], None]):
        """Set a callback function to receive audio chunks in real-time"""
        self.chunk_callback = callback
    
    def start_recording(self, streaming=False):
        """
        Start recording audio from the default microphone
        
        Args:
            streaming: If True, enables real-time chunk processing via callback
        """
        if self.is_recording:
            return
            
        self.is_recording = True
        self.is_streaming = streaming
        self.audio_queue = queue.Queue()
        
        # Start recording in a separate thread
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.start()
    
    def _record(self):
        """Internal method to record audio continuously"""
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio callback status: {status}")
            
            if self.is_recording:
                # Convert to mono if stereo
                if indata.ndim > 1:
                    audio_chunk = np.mean(indata, axis=1)
                else:
                    audio_chunk = indata.flatten()
                
                # Store for batch processing
                self.audio_queue.put(audio_chunk.copy())
                
                # If streaming, also send to callback
                if self.is_streaming and self.chunk_callback:
                    try:
                        self.chunk_callback(audio_chunk.copy())
                    except Exception as e:
                        logger.exception(f"Error in chunk callback: {e}")
        
        try:
            # Use chunk_size as blocksize for consistent chunk timing
            with sd.InputStream(
                callback=audio_callback,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                blocksize=self.chunk_size  # This ensures consistent chunk sizes
            ):
                while self.is_recording:
                    sd.sleep(100)  # Sleep for 100ms
        except Exception as e:
            logger.exception(f"Recording error: {e}")
    
    def stop_recording(self) -> Optional[np.ndarray]:
        """Stop recording and return the recorded audio data"""
        if not self.is_recording:
            return None
            
        self.is_recording = False
        self.is_streaming = False
        
        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join()
        
        # Collect all audio chunks
        audio_chunks = []
        while not self.audio_queue.empty():
            try:
                chunk = self.audio_queue.get_nowait()
                audio_chunks.append(chunk)
            except queue.Empty:
                break
        
        if not audio_chunks:
            return None
        
        # Concatenate all chunks into a single array
        audio_data = np.concatenate(audio_chunks, axis=0)
        
        return audio_data
    
    def start_streaming_recording(self, chunk_callback: Callable[[np.ndarray], None]):
        """
        Start streaming recording with real-time chunk processing
        
        Args:
            chunk_callback: Function to call with each audio chunk
        """
        self.set_chunk_callback(chunk_callback)
        self.start_recording(streaming=True)
    
    def get_available_devices(self):
        """Get list of available audio input devices"""
        devices = sd.query_devices()
        input_devices = []
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({
                    'id': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })
        
        return input_devices
    
    def set_device(self, device_id: int):
        """Set the audio input device by ID"""
        try:
            sd.default.device[0] = device_id  # Set input device
            return True
        except Exception as e:
            logger.exception(f"Error setting device: {e}")
            return False