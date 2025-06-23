import logging
import signal
from typing import Optional

import pyperclip
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from .audio_recorder import AudioRecorder
from .dbus_window_manager import DBusWindowManager
from .system_tray import SystemTrayIcon
from .transcriber import Transcriber

logger = logging.getLogger(__name__)


class VoxVibeService(QObject):
    """Main service class that manages the VoxVibe background service"""
    
    shutdown_requested = pyqtSignal()
    
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.tray_icon: Optional[SystemTrayIcon] = None
        self.audio_recorder: Optional[AudioRecorder] = None
        self.transcriber: Optional[Transcriber] = None
        self.window_manager: Optional[DBusWindowManager] = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self._initialize_components()
        
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_requested.emit()
        
    def _initialize_components(self):
        """Initialize all service components"""
        try:
            # Initialize transcriber
            self.transcriber = Transcriber()
            
            # Initialize audio recorder
            self.audio_recorder = AudioRecorder()
            
            # Initialize window manager
            self.window_manager = DBusWindowManager()
            
            # Initialize system tray
            self.tray_icon = SystemTrayIcon(service_mode=True)
            self._connect_tray_signals()
            
            # Connect shutdown signal
            self.shutdown_requested.connect(self._shutdown)
            
            logger.info("VoxVibe service components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize service components: {e}")
            self.shutdown_requested.emit()
            
    def _connect_tray_signals(self):
        """Connect system tray signals to service methods"""
        if not self.tray_icon:
            return
            
        self.tray_icon.start_recording_requested.connect(self._start_recording)
        self.tray_icon.stop_recording_requested.connect(self._stop_recording)
        self.tray_icon.settings_requested.connect(self._show_settings)
        self.tray_icon.history_requested.connect(self._show_history)
        self.tray_icon.quit_requested.connect(self.shutdown_requested.emit)
        
    def start(self):
        """Start the service"""
        if not self.tray_icon:
            logger.error("System tray not initialized")
            return False
            
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.error("System tray not available")
            return False
            
        self.tray_icon.show()
        self.tray_icon.showMessage(
            "VoxVibe",
            "Voice dictation service started",
            SystemTrayIcon.MessageIcon.Information,
            2000
        )
        
        logger.info("VoxVibe service started")
        return True
        
    def _start_recording(self):
        """Start audio recording"""
        if not self.audio_recorder or not self.window_manager:
            logger.error("Components not initialized")
            return
            
        try:
            # Store current window before recording
            self.window_manager.store_current_window()
            logger.info("Stored current window for later focus")
            
            # Update tray icon state
            self.tray_icon.set_recording_state("recording")
            
            # Start recording
            self.audio_recorder.start_recording()
            logger.info("Recording started")
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.tray_icon.set_recording_state("idle")
            
    def _stop_recording(self):
        """Stop audio recording and process transcription"""
        if not self.audio_recorder or not self.transcriber:
            logger.error("Components not initialized")
            return
            
        try:
            # Stop recording and get audio data
            self.tray_icon.set_recording_state("processing")
            audio_data = self.audio_recorder.stop_recording()
            
            if audio_data is None or len(audio_data) == 0:
                logger.warning("No audio data recorded")
                self.tray_icon.set_recording_state("idle")
                return
                
            # Transcribe audio
            transcription = self.transcriber.transcribe(audio_data)
            
            if transcription and transcription.strip():
                # Focus original window and paste text
                self._paste_transcription(transcription.strip())
                logger.info(f"Transcription completed: {transcription[:50]}...")
            else:
                logger.warning("No transcription generated")
                
        except Exception as e:
            logger.error(f"Failed during recording processing: {e}")
        finally:
            self.tray_icon.set_recording_state("idle")
            
    def _paste_transcription(self, text: str):
        """Paste transcription to the previously focused window"""
        if not self.window_manager:
            logger.warning("No window manager available")
            return
            
        try:
            success = self.window_manager.focus_and_paste(text)
            if success:
                logger.info("Text pasted successfully")
            else:
                logger.warning("Failed to paste text, falling back to clipboard")
                # Fallback: copy to clipboard
                pyperclip.copy(text)
                self.tray_icon.showMessage(
                    "VoxVibe",
                    "Transcription copied to clipboard",
                    SystemTrayIcon.MessageIcon.Information,
                    3000
                )
                
        except Exception as e:
            logger.error(f"Failed to paste transcription: {e}")
            # Fallback: copy to clipboard
            try:
                pyperclip.copy(text)
                self.tray_icon.showMessage(
                    "VoxVibe",
                    "Transcription copied to clipboard (fallback)",
                    SystemTrayIcon.MessageIcon.Information,
                    3000
                )
            except Exception as fallback_error:
                logger.error(f"Even fallback clipboard copy failed: {fallback_error}")
            
    def _show_settings(self):
        """Show settings dialog (placeholder for future implementation)"""
        self.tray_icon.showMessage(
            "VoxVibe",
            "Settings dialog - Coming Soon!",
            SystemTrayIcon.MessageIcon.Information,
            2000
        )
        
    def _show_history(self):
        """Show transcription history (placeholder for future implementation)"""
        self.tray_icon.showMessage(
            "VoxVibe",
            "History dialog - Coming Soon!",
            SystemTrayIcon.MessageIcon.Information,
            2000
        )
        
    def _shutdown(self):
        """Gracefully shutdown the service"""
        logger.info("Shutting down VoxVibe service...")
        
        # Stop any ongoing recording
        if self.audio_recorder and self.audio_recorder.is_recording:
            self.audio_recorder.stop_recording()
            
        # Hide tray icon
        if self.tray_icon:
            self.tray_icon.hide()
            
        # Quit application
        QTimer.singleShot(100, self.app.quit)