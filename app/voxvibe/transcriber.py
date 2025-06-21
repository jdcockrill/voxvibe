import asyncio
import logging
from typing import AsyncIterator, Callable, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    from whisperflow import TranscribeSession
    WHISPERFLOW_AVAILABLE = True
    logger.info("whisperflow library successfully imported")
except ImportError as e:
    logger.warning(f"whisperflow library not available: {e}")
    WHISPERFLOW_AVAILABLE = False
    
    # Create a placeholder class for development
    class TranscribeSession:
        def __init__(self, *args, **kwargs):
            raise ImportError("whisperflow library not installed")


class StreamingTranscriber:
    def __init__(self, model_size="base.en", device="auto", compute_type="auto"):
        """
        Initialize the streaming Whisper transcriber using whisper-flow.
        
        Args:
            model_size: Size of the Whisper model (default: "base.en")
            device: Device to run on ("cpu", "cuda", "auto")
            compute_type: Compute type ("int8", "int16", "float16", "float32", "auto")
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.session = None
        self.event_callbacks = []  # List of callbacks for transcript events
        
        # Initialize session lazily
        self._init_session()
    
    def _init_session(self):
        """Initialize the TranscribeSession"""
        if not WHISPERFLOW_AVAILABLE:
            logger.error("whisperflow library not available - streaming transcription disabled")
            self.session = None
            return
            
        try:
            logger.info(f"Initializing whisper-flow session with model: {self.model_size}")
            
            # Use CPU for better compatibility
            if self.device == "auto":
                device = "cpu"
            else:
                device = self.device
            
            if self.compute_type == "auto":
                compute_type = "int8" if device == "cpu" else "float16"
            else:
                compute_type = self.compute_type
            
            # Initialize based on common whisper-flow patterns
            # Note: This API may need adjustment based on actual whisperflow documentation
            self.session = TranscribeSession(
                model=self.model_size,
                device=device,
                compute_type=compute_type,
                sample_rate=16000,
                chunk_size=320,  # 320ms chunks as required
            )
            logger.info(f"Session initialized successfully on {device} with {compute_type}")
            
        except Exception as e:
            logger.exception(f"Error initializing whisper-flow session: {e}")
            logger.warning("Streaming transcription will be disabled")
            self.session = None
    
    def add_event_callback(self, callback: Callable[[str, bool], None]):
        """
        Add a callback function for transcript events.
        
        Args:
            callback: Function that takes (text, is_partial) parameters
        """
        self.event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable[[str, bool], None]):
        """Remove a callback function"""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    def _emit_event(self, text: str, is_partial: bool):
        """Emit transcript event to all registered callbacks"""
        for callback in self.event_callbacks:
            try:
                callback(text, is_partial)
            except Exception as e:
                logger.exception(f"Event callback error: {e}")
    
    async def stream_transcribe(self, audio_chunks: AsyncIterator[np.ndarray]) -> AsyncIterator[Tuple[str, bool]]:
        """
        Stream transcribe audio chunks and yield partial/final transcripts.
        
        Args:
            audio_chunks: Async iterator of audio chunks (float32, mono, 16kHz)
            
        Yields:
            Tuples of (text, is_partial) where is_partial indicates if this is a partial result
        """
        if self.session is None:
            logger.warning("Session not initialized - streaming transcription disabled")
            return
        
        try:
            async for chunk in audio_chunks:
                # Ensure audio is in the correct format
                if chunk.dtype != np.float32:
                    chunk = chunk.astype(np.float32)
                
                # Normalize audio if needed
                if np.max(np.abs(chunk)) > 1.0:
                    chunk = chunk / np.max(np.abs(chunk))
                
                # Process chunk through whisper-flow
                # Note: API calls may need adjustment based on actual whisperflow documentation
                try:
                    # Try different possible API patterns
                    if hasattr(self.session, 'transcribe_chunk'):
                        results = await self.session.transcribe_chunk(chunk)
                    elif hasattr(self.session, 'process_audio'):
                        results = await self.session.process_audio(chunk)
                    elif hasattr(self.session, 'stream'):
                        results = await self.session.stream(chunk)
                    else:
                        logger.error("Unknown whisperflow API - no suitable method found")
                        break
                    
                    # Handle different result formats
                    if isinstance(results, dict):
                        results = [results]
                    elif isinstance(results, str):
                        results = [{'text': results, 'is_partial': True}]
                    
                    for result in results:
                        if isinstance(result, dict):
                            text = result.get('text', '').strip()
                            is_partial = result.get('is_partial', True)
                        elif isinstance(result, str):
                            text = result.strip()
                            is_partial = True
                        else:
                            continue
                        
                        if text:
                            self._emit_event(text, is_partial)
                            yield (text, is_partial)
                            
                except Exception as chunk_error:
                    logger.exception(f"Error processing chunk: {chunk_error}")
                    continue
                        
        except Exception as e:
            logger.exception(f"Streaming transcription error: {e}")
    
    def transcribe_batch(self, audio_data: np.ndarray, language="en") -> Optional[str]:
        """
        Batch transcribe audio data (for backward compatibility).
        
        Args:
            audio_data: Numpy array of audio data (float32, mono, 16kHz)
            language: Language code ("en", "es", "fr", etc.)
            
        Returns:
            Transcribed text or None if transcription failed
        """
        if self.session is None:
            logger.warning("Session not initialized - batch transcription disabled")
            return None
        
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
            
            # Batch transcribe using whisper-flow
            # Note: API calls may need adjustment based on actual whisperflow documentation
            try:
                # Try different possible API patterns for batch transcription
                if hasattr(self.session, 'transcribe'):
                    result = self.session.transcribe(audio_data, language=language)
                elif hasattr(self.session, 'transcribe_batch'):
                    result = self.session.transcribe_batch(audio_data, language=language)
                elif hasattr(self.session, 'process'):
                    result = self.session.process(audio_data, language=language)
                else:
                    logger.error("Unknown whisperflow batch API - no suitable method found")
                    return None
                
                # Handle different result formats
                if isinstance(result, str):
                    text = result.strip()
                elif isinstance(result, dict) and 'text' in result:
                    text = result['text'].strip()
                elif isinstance(result, list) and result:
                    # Join multiple segments
                    text_parts = []
                    for segment in result:
                        if isinstance(segment, dict) and 'text' in segment:
                            text_parts.append(segment['text'])
                        elif isinstance(segment, str):
                            text_parts.append(segment)
                    text = ' '.join(text_parts).strip()
                else:
                    logger.warning("Unknown result format from whisperflow")
                    return None
                
                if text:
                    logger.info(f"Batch transcribed: {text}")
                    self._emit_event(text, False)  # Final result
                    return text
                
            except Exception as api_error:
                logger.exception(f"whisperflow API error: {api_error}")
                return None
            
            logger.warning("Empty transcription result")
            return None
                
        except Exception as e:
            logger.exception(f"Batch transcription error: {e}")
            return None
    
    def get_available_models(self):
        """Get list of available Whisper model sizes"""
        return [
            "tiny.en",
            "base.en",
            "small.en",
            "medium.en",
            "tiny",
            "base",
            "small",
            "medium",
            "large-v2",
            "large-v3"
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


# Backward compatibility class
class Transcriber(StreamingTranscriber):
    """Backward compatibility wrapper for the old Transcriber interface"""
    
    def __init__(self, model_size="base.en", device="auto", compute_type="auto"):
        # Map old model names to new ones
        if model_size == "base":
            model_size = "base.en"
        super().__init__(model_size, device, compute_type)
    
    def transcribe(self, audio_data: np.ndarray, language="en") -> Optional[str]:
        """Transcribe audio data to text (batch mode for backward compatibility)"""
        return self.transcribe_batch(audio_data, language)