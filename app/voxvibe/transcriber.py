import logging
import os
import time
import threading
from typing import Optional, Iterator, Tuple

import numpy as np

from .event_bus import (
    emit_partial_transcript,
    emit_final_transcript,
    emit_transcription_started,
    emit_transcription_ended,
    emit_transcription_error
)

logger = logging.getLogger(__name__)


class StreamingTranscriber:
    def __init__(self, model_size="base", device="auto", compute_type="auto", language="en"):
        """
        Initialize the streaming Whisper transcriber with whisper_streaming.
        
        Args:
            model_size: Size of the Whisper model ("tiny", "base", "small", "medium", "large-v2", "large-v3")
            device: Device to run on ("cpu", "cuda", "auto")
            compute_type: Compute type ("int8", "int16", "float16", "float32", "auto")
            language: Language code ("en", "es", "fr", etc.)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        
        # Streaming components - will be initialized lazily
        self.asr = None
        self.online_asr = None
        self.is_streaming = False
        
        # Audio configuration for streaming
        self.sample_rate = 16000
        self.chunk_duration = 0.32  # 320ms chunks as required
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
        # Buffer for collecting final transcript
        self.final_transcript_buffer = ""
        self.last_partial_text = ""
        
        # Initialize streaming components lazily
        self._initialize_streaming()
    
    def _initialize_streaming(self):
        """Initialize the whisper_streaming components with graceful fallback"""
        try:
            # Try to import whisper_streaming
            from whisper_online import OnlineASRProcessor, FasterWhisperASR
            
            logger.info(f"Initializing streaming Whisper model: {self.model_size}")
            
            # Determine device and compute type
            if self.device == "auto":
                device = "cpu"  # Use CPU for better compatibility
            else:
                device = self.device
            
            if self.compute_type == "auto":
                compute_type = "int8" if device == "cpu" else "float16"
            else:
                compute_type = self.compute_type
            
            # Initialize FasterWhisperASR backend
            self.asr = FasterWhisperASR(
                model_size=self.model_size,
                device=device,
                compute_type=compute_type,
                language=self.language,
                condition_on_previous_text=True,
                no_speech_threshold=0.6,
                logprob_threshold=-1.0,
                compression_ratio_threshold=2.4,
            )
            
            # Initialize OnlineASRProcessor
            self.online_asr = OnlineASRProcessor(
                asr=self.asr,
                tokenizer=None,  # Use default tokenizer
                buffer_trimming=("segment", 15),  # Keep last 15 seconds
                logfile=None,
                min_chunk_size=0.1  # 100ms minimum chunks for better responsiveness
            )
            
            logger.info(f"Streaming model loaded successfully on {device} with {compute_type}")
            
        except ImportError as e:
            logger.error(f"whisper_streaming not available: {e}")
            # Fallback to regular faster-whisper for compatibility
            self._initialize_fallback()
        except Exception as e:
            logger.exception(f"Error initializing streaming model: {e}")
            # Fallback to regular faster-whisper
            self._initialize_fallback()
    
    def _initialize_fallback(self):
        """Fallback to regular faster-whisper if streaming is not available"""
        try:
            from faster_whisper import WhisperModel
            
            logger.warning("Falling back to batch faster-whisper processing")
            
            # Determine device and compute type
            if self.device == "auto":
                device = "cpu"
            else:
                device = self.device
            
            if self.compute_type == "auto":
                compute_type = "int8" if device == "cpu" else "float16"
            else:
                compute_type = self.compute_type
            
            self.fallback_model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type,
                download_root=os.path.expanduser("~/.cache/whisper")
            )
            
            logger.info(f"Fallback model loaded successfully on {device} with {compute_type}")
            
        except Exception as e:
            logger.exception(f"Error loading fallback model: {e}")
            raise
    
    def start_streaming(self):
        """Start streaming transcription mode"""
        if self.online_asr is None:
            logger.warning("Streaming not available, using fallback mode")
            return
        
        self.is_streaming = True
        self.final_transcript_buffer = ""
        self.last_partial_text = ""
        emit_transcription_started()
        logger.info("Started streaming transcription")
    
    def stop_streaming(self) -> str:
        """Stop streaming transcription mode and return final transcript"""
        if not self.is_streaming:
            return self.final_transcript_buffer
        
        self.is_streaming = False
        
        # Process any remaining audio
        if self.online_asr:
            try:
                # Flush remaining audio
                result = self.online_asr.process_iter()
                if result[0] is not None:
                    partial, final = result
                    if final:
                        self.final_transcript_buffer += " " + final
                        emit_final_transcript(final)
            except Exception as e:
                logger.exception(f"Error during streaming stop: {e}")
        
        emit_transcription_ended()
        logger.info(f"Stopped streaming transcription. Final: {self.final_transcript_buffer}")
        return self.final_transcript_buffer.strip()
    
    def process_audio_chunk(self, audio_chunk: np.ndarray):
        """Process a single audio chunk for streaming transcription"""
        if not self.is_streaming or self.online_asr is None:
            return
        
        try:
            # Ensure audio is in the correct format
            if isinstance(audio_chunk, bytes):
                # Convert from bytes if needed
                audio_chunk = np.frombuffer(audio_chunk, dtype=np.int16)
                audio_chunk = audio_chunk.astype(np.float32) / 32768.0
            else:
                audio_chunk = np.array(audio_chunk, dtype=np.float32)
            
            # Normalize if needed
            if len(audio_chunk) > 0 and np.max(np.abs(audio_chunk)) > 1.0:
                audio_chunk = audio_chunk / np.max(np.abs(audio_chunk))
            
            # Insert audio chunk into processor
            self.online_asr.insert_audio_chunk(audio_chunk)
            
            # Try to get transcription results
            result = self.online_asr.process_iter()
            
            if result[0] is not None:
                partial, final = result
                
                # Handle final transcript
                if final and final.strip():
                    final_text = final.strip()
                    self.final_transcript_buffer += " " + final_text
                    emit_final_transcript(final_text)
                    logger.debug(f"Final transcript: {final_text}")
                
                # Handle partial transcript
                elif partial and partial.strip() and partial != self.last_partial_text:
                    partial_text = partial.strip()
                    self.last_partial_text = partial_text
                    emit_partial_transcript(partial_text)
                    logger.debug(f"Partial transcript: {partial_text}")
        
        except Exception as e:
            logger.exception(f"Error processing audio chunk: {e}")
            emit_transcription_error(str(e))
    
    def transcribe_batch(self, audio_data: np.ndarray, language="en") -> Optional[str]:
        """
        Fallback batch transcription for compatibility.
        
        Args:
            audio_data: Numpy array of audio data (float32, mono, 16kHz)
            language: Language code ("en", "es", "fr", etc.) or "auto" for auto-detection
            
        Returns:
            Transcribed text or None if transcription failed
        """
        if hasattr(self, 'fallback_model') and self.fallback_model is not None:
            return self._transcribe_with_fallback(audio_data, language)
        elif self.asr is not None:
            # Use the streaming ASR for batch processing if available
            return self._transcribe_with_streaming_asr(audio_data, language)
        else:
            logger.error("No transcription backend available")
            return None
    
    def _transcribe_with_fallback(self, audio_data: np.ndarray, language="en") -> Optional[str]:
        """Transcribe using fallback faster-whisper model"""
        if audio_data is None or len(audio_data) == 0:
            logger.warning("No audio data provided")
            return None
        
        try:
            # Ensure audio is in the correct format
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio if needed
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Check minimum length (at least 0.1 seconds)
            min_samples = int(0.1 * 16000)  # 0.1 seconds at 16kHz
            if len(audio_data) < min_samples:
                logger.warning("Audio too short for transcription")
                return None
            
            # Transcribe using faster-whisper
            segments, info = self.fallback_model.transcribe(
                audio_data,
                language=language if language != "auto" else None,
                beam_size=5,
                best_of=5,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    max_speech_duration_s=30
                )
            )
            
            # Combine all segments into a single text
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            if not text_parts:
                logger.warning("No speech detected in audio")
                return None
            
            full_text = " ".join(text_parts).strip()
            
            if full_text:
                logger.info(f"Transcribed ({info.language}, {info.language_probability:.2f}): {full_text}")
                return full_text
            else:
                logger.warning("Empty transcription result")
                return None
                
        except Exception as e:
            logger.exception(f"Transcription error: {e}")
            return None
    
    def _transcribe_with_streaming_asr(self, audio_data: np.ndarray, language="en") -> Optional[str]:
        """Transcribe using streaming ASR backend in batch mode"""
        # This is a simplified batch mode using the streaming backend
        # In practice, this might not be as efficient as the dedicated batch API
        logger.warning("Using streaming ASR for batch transcription - consider using streaming mode")
        
        # For now, process the entire audio as one chunk
        # This is not optimal but provides compatibility
        try:
            # Create a temporary processor for batch processing
            from whisper_online import OnlineASRProcessor
            
            temp_processor = OnlineASRProcessor(
                asr=self.asr,
                tokenizer=None,
                buffer_trimming=("segment", 30),  # Longer buffer for batch
                logfile=None
            )
            
            # Process the entire audio
            temp_processor.insert_audio_chunk(audio_data)
            result = temp_processor.process_iter()
            
            if result[0] is not None:
                partial, final = result
                return final if final else partial
            
            return None
            
        except Exception as e:
            logger.exception(f"Error in batch transcription with streaming ASR: {e}")
            return None
    
    def get_available_models(self):
        """Get list of available Whisper model sizes"""
        return [
            "tiny",      # ~39 MB
            "base",      # ~74 MB  
            "small",     # ~244 MB
            "medium",    # ~769 MB
            "large-v2",  # ~1550 MB
            "large-v3"   # ~1550 MB
        ]
    
    def get_supported_languages(self):
        """Get list of supported language codes"""
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", 
            "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk", 
            "el", "ms", "cs", "ro", "da", "hu", "ta", "no", "th", "ur", "hr", 
            "bg", "lt", "la", "mi", "ml", "cy", "sk", "te", "fa", "lv", "bn", 
            "sr", "az", "sl", "kn", "et", "mk", "br", "eu", "is", "hy", "ne", 
            "mn", "bs", "kk", "sq", "sw", "gl", "mr", "pa", "si", "km", "sn", 
            "yo", "so", "af", "oc", "ka", "be", "tg", "sd", "gu", "am", "yi", 
            "lo", "uz", "fo", "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", 
            "bo", "tl", "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
        ]


# Backward compatibility alias
Transcriber = StreamingTranscriber