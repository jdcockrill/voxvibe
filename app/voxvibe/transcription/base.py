"""Base transcriber class defining the interface for all transcription backends."""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class BaseTranscriber(ABC):
    """Base class for all transcription backends."""
    
    def __init__(self, config=None):
        """
        Initialize the transcriber.
        
        Args:
            config: Configuration object for the transcriber
        """
        self.config = config
        logger.info(f"Initializing {self.__class__.__name__}")
    
    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> Optional[str]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Numpy array of audio data (float32, mono, 16kHz)
            language: Language code ("en", "es", "fr", etc.) or None for auto-detection
            
        Returns:
            Transcribed text or None if transcription failed
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available model names for this transcriber."""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        pass
    
    def validate_audio(self, audio_data: np.ndarray) -> bool:
        """
        Validate audio data format and quality.
        
        Args:
            audio_data: Audio data to validate
            
        Returns:
            True if audio is valid, False otherwise
        """
        if audio_data is None or len(audio_data) == 0:
            logger.warning("No audio data provided")
            return False
            
        # Check minimum length (at least 0.1 seconds at 16kHz)
        min_samples = int(0.1 * 16000)
        if len(audio_data) < min_samples:
            logger.warning("Audio too short for transcription")
            return False
            
        return True
    
    def preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Preprocess audio data for transcription.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Preprocessed audio data
        """
        # Ensure audio is in the correct format
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Normalize audio if needed
        if np.max(np.abs(audio_data)) > 1.0:
            audio_data = audio_data / np.max(np.abs(audio_data))
            
        return audio_data