import logging
import os
from typing import Optional

import numpy as np
from faster_whisper import WhisperModel

from .config import TranscriptionConfig

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, config: Optional[TranscriptionConfig] = None):
        """
        Initialize the Whisper transcriber.

        Args:
            config: TranscriptionConfig object with transcription settings
        """
        self.config = config or TranscriptionConfig()
        self.model = None

        # Initialize model lazily to avoid long startup times
        self._load_model()

    def _load_model(self):
        """Load the Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.config.model}")

            # Use CPU for better compatibility
            if self.config.device == "auto":
                device = "cpu"
            else:
                device = self.config.device

            if self.config.compute_type == "auto":
                compute_type = "int8" if device == "cpu" else "float16"
            else:
                compute_type = self.config.compute_type

            self.model = WhisperModel(
                self.config.model,
                device=device,
                compute_type=compute_type,
                download_root=os.path.expanduser("~/.cache/whisper"),
            )
            logger.info(f"Model loaded successfully on {device} with {compute_type}")

        except Exception as e:
            logger.exception(f"Error loading Whisper model: {e}")
            raise

    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> Optional[str]:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Numpy array of audio data (float32, mono, 16kHz)
            language: Language code ("en", "es", "fr", etc.) or None to use config default

        Returns:
            Transcribed text or None if transcription failed
        """
        if self.model is None:
            logger.warning("Model not loaded")
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

            # Use provided language or fall back to config
            transcribe_language = language or self.config.language
            if transcribe_language == "auto":
                transcribe_language = None

            # Transcribe using faster-whisper
            segments, info = self.model.transcribe(
                audio_data,
                language=transcribe_language,
                beam_size=5,
                best_of=5,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(min_silence_duration_ms=500, max_speech_duration_s=30),
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

    def get_available_models(self):
        """Get list of available Whisper model sizes"""
        return [
            "tiny",  # ~39 MB
            "base",  # ~74 MB
            "small",  # ~244 MB
            "medium",  # ~769 MB
            "large-v2",  # ~1550 MB
            "large-v3",  # ~1550 MB
        ]

    def get_supported_languages(self):
        """Get list of supported language codes"""
        return [
            "en",
            "zh",
            "de",
            "es",
            "ru",
            "ko",
            "fr",
            "ja",
            "pt",
            "tr",
            "pl",
            "ca",
            "nl",
            "ar",
            "sv",
            "it",
            "id",
            "hi",
            "fi",
            "vi",
            "he",
            "uk",
            "el",
            "ms",
            "cs",
            "ro",
            "da",
            "hu",
            "ta",
            "no",
            "th",
            "ur",
            "hr",
            "bg",
            "lt",
            "la",
            "mi",
            "ml",
            "cy",
            "sk",
            "te",
            "fa",
            "lv",
            "bn",
            "sr",
            "az",
            "sl",
            "kn",
            "et",
            "mk",
            "br",
            "eu",
            "is",
            "hy",
            "ne",
            "mn",
            "bs",
            "kk",
            "sq",
            "sw",
            "gl",
            "mr",
            "pa",
            "si",
            "km",
            "sn",
            "yo",
            "so",
            "af",
            "oc",
            "ka",
            "be",
            "tg",
            "sd",
            "gu",
            "am",
            "yi",
            "lo",
            "uz",
            "fo",
            "ht",
            "ps",
            "tk",
            "nn",
            "mt",
            "sa",
            "lb",
            "my",
            "bo",
            "tl",
            "mg",
            "as",
            "tt",
            "haw",
            "ln",
            "ha",
            "ba",
            "jw",
            "su",
        ]
