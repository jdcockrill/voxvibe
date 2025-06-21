"""VoxVibe - A voice dictation application for Linux with streaming transcription."""

__version__ = "0.1.0"

from .transcriber import StreamingTranscriber, Transcriber
from .audio_recorder import AudioRecorder
from .event_bus import get_event_bus, EventType, TranscriptEvent

__all__ = [
    "StreamingTranscriber",
    "Transcriber", 
    "AudioRecorder",
    "get_event_bus",
    "EventType",
    "TranscriptEvent"
]