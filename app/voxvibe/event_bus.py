"""
Event bus system for VoxVibe streaming transcription events.
"""
import logging
from typing import Any, Callable, Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for VoxVibe transcription"""
    PARTIAL_TRANSCRIPT = "partial_transcript"
    FINAL_TRANSCRIPT = "final_transcript"
    TRANSCRIPTION_STARTED = "transcription_started"
    TRANSCRIPTION_ENDED = "transcription_ended"
    TRANSCRIPTION_ERROR = "transcription_error"


@dataclass
class TranscriptEvent:
    """Event data for transcript events"""
    event_type: EventType
    text: str
    timestamp: float
    confidence: float = 0.0
    is_final: bool = False


class EventBus:
    """Simple event bus for VoxVibe events"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[TranscriptEvent], None]]] = {}
        
    def subscribe(self, event_type: EventType, callback: Callable[[TranscriptEvent], None]):
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[TranscriptEvent], None]):
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from {event_type}")
            except ValueError:
                logger.warning(f"Callback not found for {event_type}")
    
    def emit(self, event: TranscriptEvent):
        """Emit an event to all subscribers"""
        event_type = event.event_type
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.exception(f"Error in event callback for {event_type}: {e}")
        else:
            logger.debug(f"No subscribers for {event_type}")


# Global event bus instance
_global_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus instance"""
    return _global_event_bus


def emit_partial_transcript(text: str, timestamp: float = 0.0, confidence: float = 0.0):
    """Convenience function to emit partial transcript event"""
    event = TranscriptEvent(
        event_type=EventType.PARTIAL_TRANSCRIPT,
        text=text,
        timestamp=timestamp,
        confidence=confidence,
        is_final=False
    )
    _global_event_bus.emit(event)


def emit_final_transcript(text: str, timestamp: float = 0.0, confidence: float = 0.0):
    """Convenience function to emit final transcript event"""
    event = TranscriptEvent(
        event_type=EventType.FINAL_TRANSCRIPT,
        text=text,
        timestamp=timestamp,
        confidence=confidence,
        is_final=True
    )
    _global_event_bus.emit(event)


def emit_transcription_started():
    """Convenience function to emit transcription started event"""
    event = TranscriptEvent(
        event_type=EventType.TRANSCRIPTION_STARTED,
        text="",
        timestamp=0.0
    )
    _global_event_bus.emit(event)


def emit_transcription_ended():
    """Convenience function to emit transcription ended event"""
    event = TranscriptEvent(
        event_type=EventType.TRANSCRIPTION_ENDED,
        text="",
        timestamp=0.0
    )
    _global_event_bus.emit(event)


def emit_transcription_error(error: str):
    """Convenience function to emit transcription error event"""
    event = TranscriptEvent(
        event_type=EventType.TRANSCRIPTION_ERROR,
        text=error,
        timestamp=0.0
    )
    _global_event_bus.emit(event)