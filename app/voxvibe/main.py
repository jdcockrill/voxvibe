#!/usr/bin/env python3
"""VoxVibe main application with enhanced hotkey service and persistent UI."""

import logging
import signal
import sys
import time
from pathlib import Path

from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from .audio_recorder import AudioRecorder
from .dbus_window_manager import DBusWindowManager
from .history import TranscriptionHistory
from .hotkey_service import HotkeyService, RecordingMode
from .sound_fx import SoundFX
from .theme import apply_theme
from .transcriber import Transcriber
from .tray_icon import VoxVibeTrayIcon


class RecordingThread(QThread):
    """Worker thread for audio recording using the improved timeout approach"""
    recording_finished = pyqtSignal(object, float)  # audio_data, start_time
    
    def __init__(self, transcriber: Transcriber):
        super().__init__()
        self.transcriber = transcriber
        self.recorder = AudioRecorder()
        self.should_stop = False
        self.start_time = 0
    
    def run(self):
        """Record audio until stopped - using the improved pattern"""
        print(f"🎯 RecordingThread: Starting recording session... [{time.strftime('%H:%M:%S.%f')[:-3]}]")
        print(f"🔍 DEBUG: should_stop = {self.should_stop} at start of run()")
        self.start_time = time.time()
        
        # Reset should_stop flag for new recording
        self.should_stop = False
        print(f"🔍 DEBUG: Reset should_stop = {self.should_stop}")
        
        # Start the audio recorder (this will create its own thread)
        self.recorder.start_recording()
        
        # Wait until stop is requested (but don't block the audio recording)
        # Add minimum recording duration to avoid race conditions
        min_recording_time = 0.5  # 500ms minimum to ensure audio capture
        
        while self.recorder.is_recording and (not self.should_stop or (time.time() - self.start_time) < min_recording_time):
            self.msleep(50)  # Check every 50ms
            
            # If stop was requested but we haven't reached minimum time, keep recording
            if self.should_stop and (time.time() - self.start_time) < min_recording_time:
                elapsed_time = time.time() - self.start_time
                remaining_time = min_recording_time - elapsed_time
                print(f"🎯 RecordingThread: Stop requested early, continuing for {remaining_time:.2f}s more... [{time.strftime('%H:%M:%S.%f')[:-3]}]")
                # Keep the AudioRecorder running - don't stop it yet
        
        print("🎯 RecordingThread: Stop requested, collecting audio...")
        
        # Stop recording and get audio data
        audio_data = self.recorder.stop_recording()
        
        print(f"🎯 RecordingThread: Finished, emitting results...")
        self.recording_finished.emit(audio_data, self.start_time)
    
    def stop_recording(self):
        """Signal the recording thread to stop"""
        import traceback
        print(f"🛑 RecordingThread: stop_recording called [{time.strftime('%H:%M:%S.%f')[:-3]}]")
        print("🔍 STACK TRACE - WHO CALLED stop_recording:")
        for line in traceback.format_stack()[:-1]:  # Exclude current frame
            print(f"    {line.strip()}")
        self.should_stop = True
        
        # Don't directly set is_recording=False here - let the run() method handle it
        # This prevents race conditions where we stop before audio chunks are collected


class VoxVibeApp:
    """Main VoxVibe application with all components integrated"""
    
    def __init__(self):
        # Core components
        self.app = None
        self.transcriber = Transcriber()
        self.history = TranscriptionHistory()
        
        # UI components
        # mic_bar removed - using tray icon for status
        self.tray_icon: VoxVibeTrayIcon = None
        self.sound_fx: SoundFX = None
        
        # Services
        self.hotkey_service: HotkeyService = None
        self.window_manager: DBusWindowManager = None
        
        # State
        self.current_mode = RecordingMode.IDLE
        
        # Recording thread (using improved timeout approach)
        self.recording_thread: RecordingThread = None
    
    def initialize(self):
        """Initialize all components"""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        # Create Qt application
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray
        self.app.setApplicationName("VoxVibe")
        
        # Apply theme
        apply_theme(self.app)
        
        # Initialize window manager
        try:
            self.window_manager = DBusWindowManager()
            print("✅ DBus window manager initialized")
        except Exception as e:
            print(f"⚠️ DBus window manager failed: {e}")
            self.window_manager = None
        
        # Initialize sound effects
        self.sound_fx = SoundFX()
        
        # Initialize system tray
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = VoxVibeTrayIcon(self.history, self.window_manager)
            self.setup_tray_connections()
        else:
            print("⚠️ System tray not available")
        
        # Initialize recording thread
        self.recording_thread = RecordingThread(self.transcriber)
        self.recording_thread.recording_finished.connect(self.on_recording_finished)
        
        # Initialize hotkey service
        self.hotkey_service = HotkeyService()
        self.setup_hotkey_callbacks()
        self.hotkey_service.start()
        
        print("🚀 VoxVibe initialized successfully")
    
    def setup_hotkey_callbacks(self):
        """Setup hotkey service callbacks"""
        self.hotkey_service.on_start_recording = self.start_recording
        self.hotkey_service.on_stop_recording = self.stop_recording
        self.hotkey_service.on_mode_change = self.on_mode_change
    
    def setup_tray_connections(self):
        """Setup tray icon signal connections"""
        if self.tray_icon:
            self.tray_icon.toggle_visibility_requested.connect(self.toggle_mic_bar_visibility)
            self.tray_icon.quit_requested.connect(self.quit_application)
    
    def start_recording(self):
        """Start audio recording"""
        if self.recording_thread.isRunning():
            return
        
        print("🎤 Starting recording...")
        
        # Store current window for pasting later
        if self.window_manager:
            try:
                self.window_manager.store_current_window()
                print("📋 Current window stored for pasting")
            except Exception as e:
                print(f"⚠️ Failed to store current window: {e}")
        
        self.recording_thread.start()
        
        # Play start sound
        if self.sound_fx:
            self.sound_fx.play_start()
        
        # Update UI (mic bar removed - using tray icon for status)
        
        if self.tray_icon:
            mode_name = self.hotkey_service.current_mode.value
            self.tray_icon.update_status(True, mode_name)
    
    def stop_recording(self):
        """Stop audio recording and process transcription"""
        if not self.recording_thread.isRunning():
            print("⚠️ Stop called but not currently recording")
            return
        
        import traceback
        print("🛑 Stopping recording...")
        print("🔍 STACK TRACE - WHO CALLED VoxVibeApp.stop_recording:")
        for line in traceback.format_stack()[:-1]:  # Exclude current frame
            print(f"    {line.strip()}")
        
        # Stop recording thread and WAIT for it to finish
        self.recording_thread.stop_recording()
        
        # Wait for thread to finish properly (with timeout)
        if self.recording_thread.wait(2000):  # Wait up to 2 seconds
            print("✅ Recording thread finished cleanly")
        else:
            print("⚠️ Recording thread didn't finish in time, forcing cleanup")
            # FORCE CLEANUP: Only if thread hangs
            if hasattr(self.recording_thread, 'recorder'):
                self.recording_thread.recorder.force_cleanup()
        
        # Play stop sound
        if self.sound_fx:
            self.sound_fx.play_stop()
        
        # Update UI state
        self.current_mode = RecordingMode.IDLE
        if self.tray_icon:
            self.tray_icon.update_status("Ready", False)
    
    def on_recording_finished(self, audio_data, start_time: float):
        """Handle completed recording"""
        if audio_data is not None and len(audio_data) > 0:
            print("🔄 Processing transcription...")
            duration_ms = int((time.time() - start_time) * 1000)
            text = self.transcriber.transcribe(audio_data)
            
            if text and text.strip():
                self.on_transcription_complete(text.strip(), duration_ms)
            else:
                print("❌ No speech detected in audio")
        else:
            print("❌ No audio data recorded - check microphone permissions")
    
    def on_transcription_complete(self, text: str, duration_ms: int):
        """Handle completed transcription"""
        print(f"✅ Transcription complete ({duration_ms}ms): '{text}'")
        
        # Add to history
        mode_name = self.current_mode.value
        entry_id = self.history.add_entry(text, duration_ms, mode_name)
        print(f"📚 Added to history as entry #{entry_id}")
        
        # Paste text
        if self.window_manager:
            try:
                print("📋 Attempting to paste text...")
                success = self.window_manager.focus_and_paste(text)
                if success:
                    print("✅ Text pasted successfully")
                else:
                    print("❌ Failed to paste text - DBus error")
            except Exception as e:
                print(f"❌ Error pasting text: {e}")
        else:
            print("❌ No window manager available for pasting")
        
        # Notify tray icon
        if self.tray_icon:
            self.tray_icon.notify_transcription_complete(text)
    
    def on_mode_change(self, mode: RecordingMode):
        """Handle recording mode change"""
        self.current_mode = mode
        print(f"🔄 Mode changed to: {mode.value}")
        
        # UI updates handled by tray icon
    
    def toggle_mic_bar_visibility(self):
        """Legacy method - mic bar removed"""
        print("👁️ Mic bar feature removed - using tray icon for status")
    
    def quit_application(self):
        """Quit the application"""
        print("👋 Shutting down VoxVibe...")
        
        # Stop services
        if self.hotkey_service:
            self.hotkey_service.stop()
        
        if self.recording_thread.isRunning():
            self.recording_thread.stop_recording()
        
        # Close UI components
        if self.mic_bar:
            self.mic_bar.close()
        
        if self.tray_icon:
            self.tray_icon.hide()
        
        # Quit application
        if self.app:
            self.app.quit()
    
    def run(self):
        """Run the application"""
        if not self.app:
            raise RuntimeError("Application not initialized")
        
        print("🎯 VoxVibe is running...")
        print("Hotkeys:")
        print("  • Alt+Space: Hold to talk")
        print("  • Win+Alt: Hold to talk") 
        print("  • Win+Alt+Space: Hands-free mode")
        print("  • Space: Exit hands-free mode")
        
        return self.app.exec()

    def cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up...")
        
        if self.hotkey_service:
            self.hotkey_service.stop()
        
        if self.recording_thread and self.recording_thread.isRunning():
            self.recording_thread.stop_recording()
            self.recording_thread.wait()  # Ensure thread finishes before cleanup
        
        # Close UI components
        if self.mic_bar:
            self.mic_bar.close()
        if self.tray_icon:
            self.tray_icon.hide()
        
        if self.app:
            self.app.quit()


def main():
    """Main entry point"""
    try:
        app = VoxVibeApp()
        app.initialize()
        return app.run()
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
