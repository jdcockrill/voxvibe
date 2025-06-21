import queue
import threading
from typing import Optional
import time
import gc

import numpy as np
import sounddevice as sd


class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.stream = None  # Keep reference to current stream
        
        # Set default device to None to use system default
        sd.default.samplerate = sample_rate
        sd.default.channels = channels
        sd.default.dtype = np.float32
        
    def start_recording(self):
        """Start recording audio from the default microphone"""
        if self.is_recording:
            print("⚠️ AudioRecorder: Already recording, ignoring start request")
            return
            
        # Check if previous recording thread is still alive
        if self.recording_thread and self.recording_thread.is_alive():
            print("⚠️ AudioRecorder: Previous recording thread still running, forcing cleanup")
            self.force_cleanup()
            time.sleep(0.2)  # Give cleanup time to work
            
        print("🎤 AudioRecorder: Starting recording...")
        self.is_recording = True
        self.audio_queue = queue.Queue()
        
        # Start recording in a separate thread with timeout protection
        self.recording_thread = threading.Thread(target=self._record_with_timeout)
        self.recording_thread.daemon = True  # Make it a daemon thread
        self.recording_thread.start()
        print(f"🎤 AudioRecorder: Recording thread started, is_recording={self.is_recording}")
    
    def _record_with_timeout(self):
        """Internal method with timeout protection"""
        print("🎤 AudioRecorder: _record_with_timeout thread started")
        
        try:
            # Set a timeout for the entire recording setup
            setup_timeout = 2.0  # 2 seconds max for setup
            start_time = time.time()
            
            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"Audio callback status: {status}")
                if self.is_recording:
                    self.audio_queue.put(indata.copy())
            
            print("🎤 AudioRecorder: Creating audio stream with timeout protection...")
            
            # Create stream with minimal settings
            try:
                self.stream = sd.InputStream(
                    callback=audio_callback,
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=np.float32,
                    blocksize=512,  # Smaller blocksize for responsiveness
                    latency='low'   # Request low latency
                )
                
                if time.time() - start_time > setup_timeout:
                    raise Exception("Stream creation timed out")
                
                print("🎤 AudioRecorder: Stream created, starting...")
                self.stream.start()
                print("🎤 AudioRecorder: Stream started successfully!")
                
                # Recording loop with quick exit
                print("🎤 AudioRecorder: Entering recording loop...")
                while self.is_recording:
                    time.sleep(0.01)  # Very responsive
                    
                print("🎤 AudioRecorder: Exited recording loop")
                
            except Exception as stream_error:
                print(f"❌ AudioRecorder: Stream error: {stream_error}")
                self.is_recording = False
                return
                
        except Exception as e:
            print(f"❌ AudioRecorder: Recording setup error: {e}")
            self.is_recording = False
        finally:
            print("🎤 AudioRecorder: Entering cleanup...")
            self._cleanup_stream()
            print("🎤 AudioRecorder: _record_with_timeout thread finished")
    
    def _cleanup_stream(self):
        """Clean up the audio stream"""
        if self.stream:
            try:
                print("🎤 AudioRecorder: Stopping stream...")
                self.stream.stop()
                print("🎤 AudioRecorder: Closing stream...")
                self.stream.close()
                print("✅ AudioRecorder: Stream closed successfully")
            except Exception as e:
                print(f"⚠️ AudioRecorder: Stream cleanup error: {e}")
            finally:
                self.stream = None
    
    def stop_recording(self) -> Optional[np.ndarray]:
        """Stop recording and return the recorded audio data"""
        print(f"🛑 AudioRecorder: stop_recording called, is_recording={self.is_recording}")
        
        if not self.is_recording:
            print("⚠️ AudioRecorder: Not recording, nothing to stop")
            return None
            
        print("🛑 AudioRecorder: Setting is_recording=False")
        self.is_recording = False
        
        # Wait a short time for the recording loop to exit
        if self.recording_thread:
            print("🛑 AudioRecorder: Waiting for recording thread to finish...")
            self.recording_thread.join(timeout=1.0)  # Wait up to 1 second
            
            if self.recording_thread.is_alive():
                print("⚠️ AudioRecorder: Thread still alive after timeout, forcing cleanup")
                self.force_cleanup()
            else:
                print("✅ AudioRecorder: Recording thread finished successfully")
        
        # Collect any audio chunks that might be available
        print(f"🛑 AudioRecorder: Collecting audio chunks from queue (size: {self.audio_queue.qsize()})")
        audio_chunks = []
        while not self.audio_queue.empty():
            try:
                chunk = self.audio_queue.get_nowait()
                audio_chunks.append(chunk)
            except queue.Empty:
                break
        
        print(f"🛑 AudioRecorder: Collected {len(audio_chunks)} audio chunks")
        
        if not audio_chunks:
            print("❌ AudioRecorder: No audio chunks collected")
            return None
        
        # Concatenate all chunks into a single array
        audio_data = np.concatenate(audio_chunks, axis=0)
        
        # If stereo, convert to mono by averaging channels
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        print(f"✅ AudioRecorder: Final audio data: {len(audio_data)} samples, max amplitude: {np.max(np.abs(audio_data)):.4f}")
        return audio_data
    
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
            print(f"Error setting device: {e}")
            return False
    
    def force_cleanup(self):
        """Force cleanup of all audio resources - call this to ensure microphone is released"""
        print("🧹 AudioRecorder: Force cleanup called")
        
        # Stop recording if active
        if self.is_recording:
            self.is_recording = False
        
        # Clean up the current stream
        self._cleanup_stream()
        
        # Force stop all sounddevice operations
        try:
            print("🧹 AudioRecorder: Force stopping all sounddevice streams...")
            sd.stop()  # Stop ALL sounddevice streams
            sd.default.reset()  # Reset sounddevice state
            print("✅ AudioRecorder: Force cleanup completed")
        except Exception as e:
            print(f"⚠️ AudioRecorder: Force cleanup error: {e}")
        
        # Force garbage collection
        gc.collect()
        
        # Give a moment for cleanup to take effect
        time.sleep(0.1)
        
        print("🧹 AudioRecorder: All cleanup operations completed")