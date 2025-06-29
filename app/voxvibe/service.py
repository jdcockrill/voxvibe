import logging
import signal
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from .audio_recorder import AudioRecorder
from .config import VoxVibeConfig, create_default_config, find_config_file
from .history_storage import HistoryStorage
from .hotkey_manager import AbstractHotkeyManager, create_hotkey_manager
from .state_manager import StateManager
from .system_tray import SystemTrayIcon
from .transcriber import Transcriber
from .window_manager import WindowManager

logger = logging.getLogger(__name__)


class VoxVibeService(QObject):
    """Main service class that manages the VoxVibe background service"""

    shutdown_requested = pyqtSignal()

    def __init__(self, app: QApplication, config: VoxVibeConfig):
        super().__init__()
        self.app = app
        self.config = config
        self.tray_icon: Optional[SystemTrayIcon] = None
        self.audio_recorder: Optional[AudioRecorder] = None
        self.transcriber: Optional[Transcriber] = None
        self.window_manager: Optional[WindowManager] = None
        self.hotkey_manager: Optional[AbstractHotkeyManager] = None
        self.history_storage: Optional[HistoryStorage] = None


        
        # Setup signal handlers for graceful shutdown on SIGTERM and SIGINT (Ctrl+C)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self._initialize_components()

    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_requested.emit()

    def _initialize_components(self):
        """Initialize all service components"""
        try:
            # Initialize state manager first
            self.state_manager = StateManager()

            # Initialize transcriber
            self.transcriber = Transcriber(self.config.transcription)

            # Initialize audio recorder
            self.audio_recorder = AudioRecorder(self.config.audio)

            # Initialize window manager
            self.window_manager = WindowManager(self.config.window_manager)

            # Log window manager diagnostics
            if self.window_manager.is_available():
                active_strategy = self.window_manager.get_active_strategy_name()
                available_strategies = self.window_manager.get_available_strategies()
                logger.info(f"Window manager active strategy: {active_strategy}")
                logger.info(f"Available strategies: {available_strategies}")
            else:
                logger.warning("No window manager strategies are available")
                diagnostics = self.window_manager.get_diagnostics()
                logger.debug(f"Window manager diagnostics: {diagnostics}")

            # Initialize history storage
            if self.config.history.enabled:
                self.history_storage = HistoryStorage(
                    self.config.history.storage_path,
                    self.config.history.max_entries
                )
                logger.info("History storage initialized")

            # Initialize system tray
            self.tray_icon = SystemTrayIcon(self.config.ui, service_mode=True)
            self._connect_tray_signals()
            
            # Update tray with initial history
            self._update_tray_history()

            # Initialize hotkey manager
            self.hotkey_manager = create_hotkey_manager(self.config.hotkeys)
            self._connect_hotkey_signals()

            # Connect state manager signals
            self._connect_state_signals()

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

        self.tray_icon.start_recording_requested.connect(self._start_recording_via_state)
        self.tray_icon.stop_recording_requested.connect(self._stop_recording_via_state)
        self.tray_icon.toggle_recording_requested.connect(self._toggle_recording)
        self.tray_icon.settings_requested.connect(self._show_settings)
        self.tray_icon.history_requested.connect(self._show_history)
        self.tray_icon.history_copy_requested.connect(self._on_history_copy)
        self.tray_icon.quit_requested.connect(self.shutdown_requested.emit)

    def _connect_hotkey_signals(self):
        """Connect hotkey manager signals"""
        if not self.hotkey_manager:
            return

        self.hotkey_manager.hotkey_pressed.connect(self._toggle_recording)

    def _connect_state_signals(self):
        """Connect state manager signals"""
        if not self.state_manager or not self.tray_icon:
            return

        # Update tray icon when state changes
        self.state_manager.state_changed.connect(self._on_state_changed)
        self.state_manager.processing_completed.connect(self._on_transcription_complete)
        self.state_manager.error_occurred.connect(self._on_error)

        # Connect recording workflow signals
        self.state_manager.recording_started.connect(self._do_start_recording_workflow)
        self.state_manager.recording_stopped.connect(self._do_stop_recording_workflow)

    def _on_state_changed(self, state):
        """Handle state changes"""
        if self.tray_icon:
            self.tray_icon.set_recording_state(state.value)

    def _on_transcription_complete(self, text: str):
        """Handle transcription completion"""
        success = self._paste_transcription(text)
        
        # Save to history if paste was successful and history is enabled
        if success and self.history_storage:
            if self.history_storage.save_transcription(text):
                self._update_tray_history()
                logger.info("Transcription saved to history")

    def _on_error(self, error_message: str):
        """Handle error states"""
        if self.tray_icon:
            self.tray_icon.showMessage("VoxVibe Error", error_message, SystemTrayIcon.MessageIcon.Critical, 5000)
        # Reset to idle after error
        if self.state_manager:
            QTimer.singleShot(2000, self.state_manager.reset_to_idle)

    def _do_start_recording_workflow(self):
        """Execute the recording start workflow without state management"""
        if not self.audio_recorder or not self.window_manager:
            logger.error("Components not initialized")
            if self.state_manager:
                self.state_manager.set_error("Components not initialized")
            return

        try:
            # Store current window before recording
            self.window_manager.store_current_window()
            logger.info("Stored current window for later focus")

            # Start recording
            self.audio_recorder.start_recording()
            logger.info("Recording started")

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            if self.state_manager:
                self.state_manager.set_error(f"Failed to start recording: {e}")

    def _do_stop_recording_workflow(self):
        """Execute the recording stop workflow without state management"""
        if not self.audio_recorder or not self.transcriber:
            logger.error("Components not initialized")
            if self.state_manager:
                self.state_manager.set_error("Components not initialized")
            return

        try:
            # Stop recording and get audio data
            audio_data = self.audio_recorder.stop_recording()

            if audio_data is None or len(audio_data) == 0:
                logger.warning("No audio data recorded")
                if self.state_manager:
                    self.state_manager.set_error("No audio data recorded")
                return

            # Transcribe audio
            transcription = self.transcriber.transcribe(audio_data)

            if transcription and transcription.strip():
                # Complete processing with transcription
                if self.state_manager:
                    self.state_manager.complete_processing(transcription.strip())
                logger.info(f"Transcription completed: {transcription[:50]}...")
            else:
                logger.warning("No transcription generated")
                if self.state_manager:
                    self.state_manager.set_error("No transcription generated")

        except Exception as e:
            logger.error(f"Failed during recording processing: {e}")
            if self.state_manager:
                self.state_manager.set_error(f"Recording processing failed: {e}")

    def start(self):
        """Start the service"""
        if not self.tray_icon:
            logger.error("System tray not initialized")
            return False

        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.error("System tray not available")
            return False

        self.tray_icon.show()

        if self.hotkey_manager:
            success = self.hotkey_manager.start()
            if success:
                logger.info("Global hotkey manager started")
            else:
                logger.warning("Failed to start global hotkey manager")

        logger.info("VoxVibe service started")
        return True

    def _toggle_recording(self):
        """Toggle recording state via hotkey or tray click"""
        if not self.state_manager:
            logger.error("State manager not initialized")
            return

        success = self.state_manager.toggle_recording()
        if not success:
            logger.warning("Failed to toggle recording state")

    def _start_recording_via_state(self):
        """Start recording via state manager (for direct tray menu actions)"""
        if not self.state_manager:
            logger.error("State manager not initialized")
            return
        self.state_manager.start_recording()

    def _stop_recording_via_state(self):
        """Stop recording via state manager (for direct tray menu actions)"""
        if not self.state_manager:
            logger.error("State manager not initialized")
            return
        self.state_manager.stop_recording()

    def _paste_transcription(self, text: str) -> bool:
        """Paste transcription to the previously focused window"""
        if not self.window_manager:
            logger.warning("No window manager available")
            return False

        try:
            success = self.window_manager.focus_and_paste(text)
            if success:
                logger.info("Text pasted successfully")
                return True
            else:
                logger.warning("Failed to paste text.")
                return False

        except Exception as e:
            logger.error(f"Failed to paste transcription: {e}")
            return False

    def _show_settings(self):
        """Open the `config.toml` file with the system's default editor/viewer."""
        if not self.tray_icon:
            return

        try:
            # Locate configuration file (create a default one if missing)
            config_path = find_config_file()
            if config_path is None:
                config_path = create_default_config()

            # Convert to QUrl and request the OS to open it
            url = QUrl.fromLocalFile(str(config_path))
            opened = QDesktopServices.openUrl(url)

            if opened:
                # Brief confirmation that something happened
                self.tray_icon.showMessage(
                    "VoxVibe",
                    f"Opened settings file: {config_path}",
                    SystemTrayIcon.MessageIcon.Information,
                    1500,
                )
            else:
                self.tray_icon.showMessage(
                    "VoxVibe",
                    "Failed to open settings file with default application.",
                    SystemTrayIcon.MessageIcon.Warning,
                    3000,
                )
        except Exception as e:
            logger.error(f"Error opening settings file: {e}")
            self.tray_icon.showMessage(
                "VoxVibe",
                "Error opening settings file. Check logs for details.",
                SystemTrayIcon.MessageIcon.Warning,
                3000,
            )

    def _show_history(self):
        """Show transcription history (placeholder for future implementation)"""
        self.tray_icon.showMessage(
            "VoxVibe", "History dialog - Coming Soon!", SystemTrayIcon.MessageIcon.Information, 2000
        )

    def _on_history_copy(self, text: str):
        """Handle history item copy to clipboard"""
        if self.tray_icon:
            self.tray_icon.showMessage(
                "VoxVibe", 
                f"Copied to clipboard: {text[:30]}{'...' if len(text) > 30 else ''}", 
                SystemTrayIcon.MessageIcon.Information, 
                1500
            )

    def _update_tray_history(self):
        """Update tray menu with latest history entries"""
        if not self.tray_icon or not self.history_storage:
            return
        
        try:
            # Get recent history entries
            history_entries = self.history_storage.get_recent(13)  # Get up to 13 for menu display
            self.tray_icon.update_history(history_entries)
        except Exception as e:
            logger.error(f"Failed to update tray history: {e}")

    def _shutdown(self):
        """Gracefully shutdown the service"""
        logger.info("Shutting down VoxVibe service...")

        # Stop hotkey manager
        if self.hotkey_manager:
            self.hotkey_manager.stop()

        # Stop any ongoing recording
        if self.audio_recorder and self.audio_recorder.is_recording:
            self.audio_recorder.stop_recording()

        # Hide tray icon
        if self.tray_icon:
            self.tray_icon.hide()

        # Quit application
        QTimer.singleShot(100, self.app.quit)
