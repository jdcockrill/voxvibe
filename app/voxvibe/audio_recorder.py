import logging
import queue
import threading
from typing import Optional

import numpy as np
import sounddevice as sd

from .config import AudioConfig

logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.sample_rate = self.config.sample_rate
        self.channels = self.config.channels
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None

        # Set default device to None to use system default
        sd.default.samplerate = self.sample_rate
        sd.default.channels = self.channels
        sd.default.dtype = np.float32

    def start_recording(self):
        """Start recording audio from the default microphone"""
        if self.is_recording:
            return

        self.is_recording = True
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
                self.audio_queue.put(indata.copy())

        try:
            with sd.InputStream(
                callback=audio_callback, samplerate=self.sample_rate, channels=self.channels, dtype=np.float32
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

        # If stereo, convert to mono by averaging channels
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)

        return audio_data

    def get_available_devices(self):
        """Get list of available audio input devices"""
        devices = sd.query_devices()
        input_devices = []

        for i, device in enumerate(devices):
            if device["max_input_channels"] > 0:
                input_devices.append(
                    {
                        "id": i,
                        "name": device["name"],
                        "channels": device["max_input_channels"],
                        "sample_rate": device["default_samplerate"],
                    }
                )

        return input_devices

    def set_device(self, device_id: int):
        """Set the audio input device by ID"""
        try:
            sd.default.device[0] = device_id  # Set input device
            return True
        except Exception as e:
            logger.exception(f"Error setting device: {e}")
            return False
