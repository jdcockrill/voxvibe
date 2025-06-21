import logging
import sys

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .audio_recorder import AudioRecorder
from .dbus_window_manager import DBusWindowManager
from .theme import EXTRA, apply_theme
from .transcriber import StreamingTranscriber
from .event_bus import (
    get_event_bus,
    EventType,
    TranscriptEvent
)


class StreamingRecordingThread(QThread):
    """Enhanced recording thread with streaming transcription support"""
    recording_finished = pyqtSignal(str)
    partial_transcript = pyqtSignal(str)
    final_transcript = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recorder = AudioRecorder(chunk_duration=0.32)  # 320ms chunks
        self.transcriber = StreamingTranscriber()
        self.should_stop = False
        self.accumulated_transcript = ""
        
        # Subscribe to transcript events
        event_bus = get_event_bus()
        event_bus.subscribe(EventType.PARTIAL_TRANSCRIPT, self._on_partial_transcript)
        event_bus.subscribe(EventType.FINAL_TRANSCRIPT, self._on_final_transcript)

    def run(self):
        """Main recording and streaming thread"""
        try:
            # Start streaming transcription
            self.transcriber.start_streaming()
            
            # Start recording with streaming callback
            self.recorder.start_streaming_recording(self.transcriber.process_audio_chunk)
            
            # Keep running until stopped
            while not self.should_stop:
                self.msleep(100)
            
            # Stop recording and transcription
            audio_data = self.recorder.stop_recording()
            final_transcript = self.transcriber.stop_streaming()
            
            # Use accumulated transcript or final transcript
            result_text = self.accumulated_transcript if self.accumulated_transcript else final_transcript
            self.recording_finished.emit(result_text)
            
        except Exception as e:
            logging.exception(f"Error in streaming recording: {e}")
            # Fallback to batch processing if streaming fails
            self._fallback_batch_processing()

    def _fallback_batch_processing(self):
        """Fallback to batch processing if streaming fails"""
        try:
            logging.warning("Falling back to batch processing")
            self.recorder.start_recording(streaming=False)
            
            while not self.should_stop:
                self.msleep(100)
            
            audio_data = self.recorder.stop_recording()
            if audio_data is not None:
                text = self.transcriber.transcribe_batch(audio_data)
                self.recording_finished.emit(text or "")
            else:
                self.recording_finished.emit("")
        except Exception as e:
            logging.exception(f"Error in fallback batch processing: {e}")
            self.recording_finished.emit("")

    def _on_partial_transcript(self, event: TranscriptEvent):
        """Handle partial transcript events"""
        if event.text.strip():
            self.partial_transcript.emit(event.text)

    def _on_final_transcript(self, event: TranscriptEvent):
        """Handle final transcript events"""
        if event.text.strip():
            # Accumulate final transcripts
            if self.accumulated_transcript:
                self.accumulated_transcript += " " + event.text
            else:
                self.accumulated_transcript = event.text
            self.final_transcript.emit(event.text)

    def stop_recording(self):
        """Stop the recording thread"""
        self.should_stop = True


class RecordingThread(StreamingRecordingThread):
    """Backward compatibility alias"""
    pass

class DictationApp(QWidget):
    def __init__(self, window_manager: DBusWindowManager):
        super().__init__()
        self.window_manager = window_manager
        self.recording_thread = None
        self.current_partial_text = ""
        self.setup_ui()
        self.setup_shortcuts()
        QTimer.singleShot(500, self.start_recording)

    def setup_ui(self):
        self.setWindowTitle("VoxVibe - Recording...")
        self.setGeometry(100, 100, 320, 320)  # Slightly larger for streaming feedback
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        )
        layout = self._create_main_layout()
        self.setLayout(layout)

    def _create_main_layout(self):
        layout = QVBoxLayout()
        base_padding = 20
        layout.addSpacing(base_padding)
        self.icon_label = self._create_icon_label()
        layout.addWidget(self.icon_label)
        layout.addSpacing(base_padding)
        self.status_label = self._create_status_label()
        layout.addWidget(self.status_label)
        layout.addSpacing(10)
        # Add transcript preview label
        self.transcript_label = self._create_transcript_label()
        layout.addWidget(self.transcript_label)
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
        label = QLabel("🔴 Recording... Press SPACE to stop")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        label.setFont(font)
        return label

    def _create_transcript_label(self):
        """Create label for showing partial transcripts"""
        label = QLabel("")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        font = QFont()
        font.setPointSize(11)
        label.setFont(font)
        label.setMinimumHeight(40)
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
        """Start streaming recording with real-time feedback"""
        self.recording_thread = StreamingRecordingThread()
        
        # Connect all signals for streaming feedback
        self.recording_thread.recording_finished.connect(self.on_recording_finished)
        self.recording_thread.partial_transcript.connect(self.on_partial_transcript)
        self.recording_thread.final_transcript.connect(self.on_final_transcript)
        
        self.recording_thread.start()

    def stop_recording(self):
        if self.recording_thread and self.recording_thread.isRunning():
            self.status_label.setText("⏹️ Stopping recording...")
            self.transcript_label.setText("")
            self.recording_thread.stop_recording()

    def on_partial_transcript(self, text: str):
        """Handle partial transcript updates for real-time feedback"""
        if text.strip():
            self.current_partial_text = text
            # Show partial text with visual indication it's tentative
            display_text = f"🔄 {text}..."
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."
            self.transcript_label.setText(display_text)
            QApplication.processEvents()

    def on_final_transcript(self, text: str):
        """Handle final transcript segments"""
        if text.strip():
            # Show final text with checkmark
            display_text = f"✅ {text}"
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."
            self.transcript_label.setText(display_text)
            QApplication.processEvents()
            
            # Clear after a short delay to show next partial
            QTimer.singleShot(1000, lambda: self.transcript_label.setText(""))

    def on_recording_finished(self, final_text: str):
        """Handle completion of recording and transcription"""
        if final_text and final_text.strip():
            self.status_label.setText("✅ Transcription complete")
            self.transcript_label.setText(f"Final: {final_text[:40]}...")
            self.hide()
            QApplication.processEvents()
            QTimer.singleShot(500, lambda: self.paste_and_close(final_text.strip()))
        else:
            self.status_label.setText("❌ No speech detected")
            self.transcript_label.setText("")
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
