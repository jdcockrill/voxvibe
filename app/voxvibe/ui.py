import logging
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .dbus_window_manager import DBusWindowManager
from .event_bus import Events, event_bus
from .streaming_recorder import StreamingRecordingThread
from .theme import EXTRA, apply_theme
from .transcriber import Transcriber

# Import the streaming recording thread as RecordingThread for backward compatibility
RecordingThread = StreamingRecordingThread

class DictationApp(QWidget):
    def __init__(self, window_manager: DBusWindowManager):
        super().__init__()
        self.window_manager = window_manager
        self.recording_thread = None
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_event_listeners()
        QTimer.singleShot(500, self.start_recording)

    def setup_ui(self):
        self.setWindowTitle("Voice Flow - Recording...")
        self.setGeometry(100, 100, 280, 280)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        )
        layout = self._create_main_layout()
        self.setLayout(layout)

    def _create_main_layout(self):
        layout = QVBoxLayout()
        base_padding = 22
        layout.addSpacing(base_padding)
        self.icon_label = self._create_icon_label()
        layout.addWidget(self.icon_label)
        layout.addSpacing(base_padding)
        self.status_label = self._create_status_label()
        layout.addWidget(self.status_label)
        layout.addSpacing(base_padding)
        self.cancel_button = self._create_cancel_button()
        button_layout = self._create_button_layout(self.cancel_button)
        layout.addLayout(button_layout)
        layout.addSpacing(base_padding)
        return layout

    def _create_icon_label(self):
        label = QLabel("🎤")
        label.setStyleSheet("font-family: 'Noto Color Emoji'; font-size: 72pt;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _create_status_label(self):
        label = QLabel("Recording... Press SPACE to stop")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        label.setFont(font)
        return label

    def _create_cancel_button(self):
        button = QPushButton("Cancel (Esc)")
        button.setFixedWidth(200)
        button.setStyleSheet(f"background-color: {EXTRA['errorColor']}; color: {EXTRA['textColor']}; border-color: {EXTRA['errorColor']};")
        button.clicked.connect(self.close)
        return button

    def _create_button_layout(self, button):
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(button)
        button_layout.addStretch()
        return button_layout

    def setup_shortcuts(self):
        space_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        space_shortcut.activated.connect(self.stop_recording)
        esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc_shortcut.activated.connect(self.close)
    
    def setup_event_listeners(self):
        """Set up event bus listeners for streaming transcription events"""
        # Subscribe to transcript events (for future UI updates)
        event_bus.subscribe(Events.TRANSCRIPT_PARTIAL, self._on_partial_transcript)
        event_bus.subscribe(Events.TRANSCRIPT_FINAL, self._on_final_transcript)
        event_bus.subscribe(Events.TRANSCRIPTION_STARTED, self._on_transcription_started)
    
    def _on_partial_transcript(self, data):
        """Handle partial transcript events (placeholder for future UI updates)"""
        if data and 'text' in data:
            text = data['text']
            logging.debug(f"Partial transcript received: {text}")
            # Future UI update: could show partial results here
    
    def _on_final_transcript(self, data):
        """Handle final transcript events (placeholder for future UI updates)"""
        if data and 'text' in data:
            text = data['text']
            logging.info(f"Final transcript received: {text}")
            # Future UI update: could show final results here
    
    def _on_transcription_started(self, data):
        """Handle transcription started events"""
        logging.debug("Transcription started")
        # Update UI to show transcription in progress
        self.status_label.setText("🔄 Transcribing...")

    def start_recording(self):
        self.recording_thread = RecordingThread()
        self.recording_thread.recording_finished.connect(self.on_recording_finished)
        self.recording_thread.start()

    def stop_recording(self):
        if self.recording_thread and self.recording_thread.isRunning():
            self.status_label.setText("⏹️ Stopping recording...")
            self.recording_thread.stop_recording()

    def on_recording_finished(self, result):
        """Handle recording finished - result is now the final transcribed text"""
        if result and isinstance(result, str) and result.strip():
            # We have a transcribed text result
            text = result.strip()
            self.hide()
            QApplication.processEvents()
            QTimer.singleShot(500, lambda: self.paste_and_close(text))
        elif result is None:
            self.status_label.setText("❌ Recording failed")
            QTimer.singleShot(2000, self.close)
        else:
            self.status_label.setText("❌ No speech detected")
            QTimer.singleShot(2000, self.close)

    def paste_and_close(self, text: str):
        if self.window_manager:
            success = self.window_manager.focus_and_paste(text)
            if success:
                logging.info("✅ Focused previous window and pasted text via DBus")
            else:
                logging.warning("❌ DBus FocusAndPaste failed; text was not pasted")
        else:
            logging.info(f"Text ready to paste: {text[:50]}...")
        QTimer.singleShot(200, self._close_and_quit)

    def _close_and_quit(self):
        self.close()
        # Ensure the Qt event loop terminates
        # Bit of a hack, probably down to the Whisper transcription having its own internal threads.
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def closeEvent(self, event):
        if self.recording_thread and self.recording_thread.isRunning():
            self.recording_thread.stop_recording()
            self.recording_thread.wait()
        event.accept()
