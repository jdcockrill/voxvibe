"""Transcription package for VoxVibe supporting multiple backends."""

from .base import BaseTranscriber
from .voxtral_transcriber import VoxtralTranscriber
from .whisper_transcriber import WhisperTranscriber

__all__ = ["BaseTranscriber", "WhisperTranscriber", "VoxtralTranscriber"]