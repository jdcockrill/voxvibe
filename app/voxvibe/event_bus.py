import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class EventBus:
    """Simple event bus for handling transcript events and other application events."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, callback: Callable[[Any], None]):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to (e.g., 'transcript_partial', 'transcript_final')
            callback: Function to call when event is emitted
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]):
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to remove from subscribers
        """
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from event: {event_type}")
    
    def emit(self, event_type: str, data: Any = None):
        """
        Emit an event to all subscribers.
        
        Args:
            event_type: Type of event to emit
            data: Data to pass to subscribers
        """
        if event_type in self._subscribers:
            logger.debug(f"Emitting event: {event_type} to {len(self._subscribers[event_type])} subscribers")
            for callback in self._subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.exception(f"Error in event callback for {event_type}: {e}")
    
    def clear_subscribers(self, event_type: str = None):
        """
        Clear all subscribers for a specific event type, or all subscribers.
        
        Args:
            event_type: Specific event type to clear, or None to clear all
        """
        if event_type:
            if event_type in self._subscribers:
                self._subscribers[event_type].clear()
                logger.debug(f"Cleared subscribers for event: {event_type}")
        else:
            self._subscribers.clear()
            logger.debug("Cleared all event subscribers")


# Global event bus instance
event_bus = EventBus()


# Event type constants
class Events:
    TRANSCRIPT_PARTIAL = "transcript_partial"
    TRANSCRIPT_FINAL = "transcript_final"
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    TRANSCRIPTION_STARTED = "transcription_started"
    TRANSCRIPTION_COMPLETED = "transcription_completed"
    ERROR = "error"