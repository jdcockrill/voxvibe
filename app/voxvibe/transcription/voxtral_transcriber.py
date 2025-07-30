"""Voxtral transcriber using Mistral's audio transcription API."""

import io
import logging
from typing import List, Optional

import numpy as np
import soundfile as sf
from mistralai import Mistral

from .base import BaseTranscriber

logger = logging.getLogger(__name__)


class VoxtralTranscriber(BaseTranscriber):
    """Transcriber using Mistral's Voxtral API for speech-to-text."""
    
    def __init__(self, config=None):
        """
        Initialize the Voxtral transcriber.

        Args:
            config: Configuration object with voxtral settings
        """
        super().__init__(config)
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Mistral client for Voxtral API."""
        try:
            if not hasattr(self.config, 'voxtral'):
                raise ValueError("VoxtralTranscriber requires voxtral configuration")
            
            api_key = getattr(self.config.voxtral, 'api_key', None)
            if not api_key:
                raise ValueError("Voxtral API key is required")
            
            self.client = Mistral(api_key=api_key)
            logger.info("Voxtral client initialized successfully")
            
        except Exception as e:
            logger.exception(f"Error initializing Voxtral client: {e}")
            raise

    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> Optional[str]:
        """
        Transcribe audio data to text using Voxtral API.

        Args:
            audio_data: Numpy array of audio data (float32, mono, 16kHz)
            language: Language code ("en", "es", "fr", etc.) - currently not used by Voxtral

        Returns:
            Transcribed text or None if transcription failed
        """
        if self.client is None:
            logger.warning("Voxtral client not initialized")
            return None

        if not self.validate_audio(audio_data):
            return None

        try:
            # Preprocess audio
            audio_data = self.preprocess_audio(audio_data)

            # Convert numpy array to audio file bytes
            audio_bytes = self._numpy_to_audio_bytes(audio_data)
            
            # Use the voxtral-mini-latest model for transcription
            model = getattr(self.config.voxtral, 'model', 'voxtral-mini-latest')
            
            # Call Mistral's audio transcription API
            response = self.client.audio.transcriptions.complete(
                model=model,
                file={
                    "content": audio_bytes,
                    "file_name": "audio.wav",
                }
            )
            
            if hasattr(response, 'text') and response.text:
                transcribed_text = response.text.strip()
                logger.info(f"Voxtral transcribed: {transcribed_text}")
                return transcribed_text
            elif isinstance(response, str):
                transcribed_text = response.strip()
                logger.info(f"Voxtral transcribed: {transcribed_text}")
                return transcribed_text
            else:
                logger.warning("Empty transcription result from Voxtral")
                return None

        except Exception as e:
            logger.exception(f"Voxtral transcription error: {e}")
            return None

    def _numpy_to_audio_bytes(self, audio_data: np.ndarray, sample_rate: int = 16000) -> bytes:
        """
        Convert numpy audio data to WAV bytes.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate for the audio
            
        Returns:
            Audio data as WAV bytes
        """
        with io.BytesIO() as buffer:
            sf.write(buffer, audio_data, sample_rate, format='WAV')
            return buffer.getvalue()

    def get_available_models(self) -> List[str]:
        """Get list of available Voxtral models."""
        return [
            "voxtral-mini-latest",  # Efficient transcription-only service
        ]

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.
        
        Note: Voxtral API handles language detection automatically,
        but we return common language codes for compatibility.
        """
        return [
            "en",  # English
            "es",  # Spanish  
            "fr",  # French
            "de",  # German
            "it",  # Italian
            "pt",  # Portuguese
            "ru",  # Russian
            "ja",  # Japanese
            "ko",  # Korean
            "zh",  # Chinese
            "ar",  # Arabic
            "hi",  # Hindi
            "nl",  # Dutch
            "pl",  # Polish
            "sv",  # Swedish
            "da",  # Danish
            "no",  # Norwegian
            "fi",  # Finnish
        ]