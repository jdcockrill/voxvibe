#!/usr/bin/env python3
import sys
import signal
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut

from .audio_recorder import AudioRecorder
from .transcriber import Transcriber
from .clipboard_manager import ClipboardManager
from .window_manager import WindowManager


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
    def __init__(self):
        super().__init__()
        self.transcriber = Transcriber()
        self.clipboard_manager = ClipboardManager()
        self.window_manager = None  # Will be set by main()
        self.recording_thread = None
        
        self.setup_ui()
        self.setup_shortcuts()
        
        # Start recording after a short delay
        QTimer.singleShot(500, self.start_recording)
    
    def setup_ui(self):
        self.setWindowTitle("Voice Flow - Recording...")
        self.setGeometry(100, 100, 400, 200)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("🎤 Recording... Press SPACE to stop")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)
        
        # Instructions
        instructions = QLabel("Speak clearly into your microphone.\nPress SPACE when finished speaking.")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        layout.addWidget(self.cancel_button)
        
        self.setLayout(layout)
    
    def setup_shortcuts(self):
        # Space key to stop recording
        space_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        space_shortcut.activated.connect(self.stop_recording)
        
        # Escape to cancel
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
            QApplication.processEvents()  # Update UI
            
            text = self.transcriber.transcribe(audio_data)
            
            if text and text.strip():
                # Copy to clipboard
                self.clipboard_manager.set_text(text.strip())
                
                # Hide the window to background it
                self.hide()
                QApplication.processEvents()
                
                # Wait a moment for focus to settle, then auto-paste
                QTimer.singleShot(500, lambda: self.paste_and_close(text.strip()))
            else:
                self.status_label.setText("❌ No speech detected")
                QTimer.singleShot(2000, self.close)
        else:
            self.status_label.setText("❌ No audio recorded")
            QTimer.singleShot(2000, self.close)
    
    def paste_and_close(self, text: str):
        """Focus previous window, auto-paste text, and close app"""
        if self.window_manager:
            # First, try to focus the previous window
            focus_success = self.window_manager.focus_previous_window()
            
            # Wait a moment for focus to settle
            if focus_success:
                QTimer.singleShot(300, lambda: self._do_paste_and_close(text))
            else:
                # If focusing failed, just try to paste anyway
                print("Focus failed, trying paste anyway...")
                self._do_paste_and_close(text)
        else:
            print(f"📋 Text copied to clipboard: {text[:50]}...")
            QTimer.singleShot(200, self.close)
    
    def _do_paste_and_close(self, text: str):
        """Actually perform the paste and close"""
        success = self.window_manager.simulate_paste()
        
        if success:
            print(f"✅ Auto-pasted: {text[:50]}...")
        else:
            print(f"❌ Auto-paste failed. Text copied to clipboard: {text[:50]}...")
        
        # Close the application
        QTimer.singleShot(200, self.close)
    
    def closeEvent(self, event):
        if self.recording_thread and self.recording_thread.isRunning():
            self.recording_thread.stop_recording()
            self.recording_thread.wait()
        event.accept()


def main():
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Store the currently active window BEFORE creating the Qt app
    window_manager = WindowManager()
    window_manager.store_current_window()
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    window = DictationApp()
    # Pass the window manager with stored window info to the app
    window.window_manager = window_manager
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
