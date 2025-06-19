import logging
import sys

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .audio_recorder import AudioRecorder
from .dbus_window_manager import DBusWindowManager
from .theme import EXTRA, apply_theme
from .transcriber import Transcriber


class RecordingThread(QThread):
    recording_finished = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.recorder = AudioRecorder()
        self.should_stop = False

    def run(self):
        self.recorder.start_recording()
        while not self.should_stop:
            self.msleep(100)
        audio_data = self.recorder.stop_recording()
        self.recording_finished.emit(audio_data)

    def stop_recording(self):
        self.should_stop = True

class DictationApp(QWidget):
    def __init__(self, window_manager: DBusWindowManager):
        super().__init__()
        self.transcriber = Transcriber()
        self.window_manager = window_manager
        self.recording_thread = None
        self.setup_ui()
        self.setup_shortcuts()
        QTimer.singleShot(500, self.start_recording)

    def setup_ui(self):
        self.setWindowTitle("Voice Flow - Recording...")
        self.setGeometry(100, 100, 280, 280)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        )
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # self.setStyleSheet("background: transparent;")
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

    def start_recording(self):
        self.recording_thread = RecordingThread()
        self.recording_thread.recording_finished.connect(self.on_recording_finished)
        self.recording_thread.start()

    def stop_recording(self):
        if self.recording_thread and self.recording_thread.isRunning():
            self.status_label.setText("⏹️ Stopping recording...")
            self.recording_thread.stop_recording()

    def on_recording_finished(self, audio_data):
        if audio_data is not None and len(audio_data) > 0:
            self.status_label.setText("🔄 Transcribing...")
            QApplication.processEvents()
            text = self.transcriber.transcribe(audio_data)
            if text and text.strip():
                self.hide()
                QApplication.processEvents()
                QTimer.singleShot(500, lambda: self.paste_and_close(text.strip()))
            else:
                self.status_label.setText("❌ No speech detected")
                QTimer.singleShot(2000, self.close)
        else:
            self.status_label.setText("❌ No audio recorded")
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
        QApplication.quit()

    def closeEvent(self, event):
        if self.recording_thread and self.recording_thread.isRunning():
            self.recording_thread.stop_recording()
            self.recording_thread.wait()
        event.accept()
