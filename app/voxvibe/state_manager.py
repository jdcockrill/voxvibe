import logging
import time
from enum import Enum
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class RecordingState(Enum):
    """Recording state enumeration"""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"


class StateManager(QObject):
    """Manages the global recording state and coordinates between components"""
    
    # Signals for state changes
    state_changed = pyqtSignal(RecordingState)
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    processing_completed = pyqtSignal(str)  # transcribed text
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self._current_state = RecordingState.IDLE
        self._last_transcription: Optional[str] = None
        self._recording_start_time: Optional[float] = None
    
    @property
    def current_state(self) -> RecordingState:
        """Get the current recording state"""
        return self._current_state
    
    @property
    def is_idle(self) -> bool:
        """Check if system is idle"""
        return self._current_state == RecordingState.IDLE
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self._current_state == RecordingState.RECORDING
    
    @property
    def is_processing(self) -> bool:
        """Check if processing transcription"""
        return self._current_state == RecordingState.PROCESSING
    
    @property
    def has_error(self) -> bool:
        """Check if in error state"""
        return self._current_state == RecordingState.ERROR
    
    @property
    def last_transcription(self) -> Optional[str]:
        """Get the last successful transcription"""
        return self._last_transcription
    
    def start_recording(self) -> bool:
        """Transition to recording state"""
        if self._current_state != RecordingState.IDLE:
            logger.warning(f"Cannot start recording from state: {self._current_state}")
            return False
        
        self._recording_start_time = time.time()
        self._set_state(RecordingState.RECORDING)
        self.recording_started.emit()
        logger.info("Recording state: started")
        return True

    def stop_recording(self) -> bool:
        """Transition from recording to processing state"""
        if self._current_state != RecordingState.RECORDING:
            logger.warning(f"Cannot stop recording from state: {self._current_state}")
            return False
        
        if self._recording_start_time:
            duration = time.time() - self._recording_start_time
            logger.info(f"Recording duration: {duration:.2f} seconds")
            self._recording_start_time = None
        
        self._set_state(RecordingState.PROCESSING)
        self.recording_stopped.emit()
        logger.info("Recording state: stopped, processing")
        return True
    
    def complete_processing(self, transcription: str) -> bool:
        """Complete processing with successful transcription"""
        if self._current_state != RecordingState.PROCESSING:
            logger.warning(f"Cannot complete processing from state: {self._current_state}")
            return False
        
        self._last_transcription = transcription if transcription else None
        self._set_state(RecordingState.IDLE)
        self.processing_completed.emit(transcription)
        logger.info(f"Processing completed: '{transcription[:50]}...' ({len(transcription)} chars)")
        return True
    
    def set_error(self, error_message: str) -> bool:
        """Set error state with message"""
        previous_state = self._current_state
        self._set_state(RecordingState.ERROR)
        self.error_occurred.emit(error_message)
        logger.error(f"State error from {previous_state}: {error_message}")
        return True
    
    def reset_to_idle(self) -> bool:
        """Force reset to idle state (for error recovery)"""
        previous_state = self._current_state
        self._recording_start_time = None
        self._set_state(RecordingState.IDLE)
        logger.info(f"State reset to idle from {previous_state}")
        return True
    
    def toggle_recording(self) -> bool:
        """Toggle recording state (start if idle, stop if recording)"""
        if self.is_idle:
            return self.start_recording()
        elif self.is_recording:
            return self.stop_recording()
        else:
            logger.warning(f"Cannot toggle recording from state: {self._current_state}")
            return False
    
    def _set_state(self, new_state: RecordingState):
        """Internal method to update state and emit signal"""
        if new_state != self._current_state:
            old_state = self._current_state
            self._current_state = new_state
            self.state_changed.emit(new_state)
            logger.debug(f"State transition: {old_state} -> {new_state}")
    
    def get_state_display_text(self) -> str:
        """Get human-readable state text for UI display"""
        state_texts = {
            RecordingState.IDLE: "Ready",
            RecordingState.RECORDING: "Recording...",
            RecordingState.PROCESSING: "Processing...",
            RecordingState.ERROR: "Error"
        }
        return state_texts.get(self._current_state, "Unknown")
    
    def get_tray_tooltip(self) -> str:
        """Get tooltip text for system tray icon"""
        base_tooltip = "VoxVibe Voice Dictation"
        state_text = self.get_state_display_text()
        
        if self.is_idle:
            return f"{base_tooltip} - {state_text}"
        else:
            return f"{base_tooltip} - {state_text}"