"""System tray icon for VoxVibe with history access and quick actions."""

import sys
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QMessageBox

from .history import TranscriptionHistory, HistoryEntry
from .dbus_window_manager import DBusWindowManager


class VoxVibeTrayIcon(QSystemTrayIcon):
    # Signals
    show_history_requested = pyqtSignal()
    paste_requested = pyqtSignal(str)  # text to paste
    toggle_visibility_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self, history: TranscriptionHistory, window_manager: Optional[DBusWindowManager] = None):
        super().__init__()
        
        self.history = history
        self.window_manager = window_manager
        
        # Create icon
        self.setIcon(self.create_microphone_icon())
        self.setToolTip("VoxVibe - Voice Transcription")
        
        # Setup context menu
        self.setup_menu()
        
        # Connect signals
        self.activated.connect(self.on_tray_activated)
        
        # Show the tray icon
        self.show()
        
        print("🎯 System tray icon initialized")
    
    def create_microphone_icon(self) -> QIcon:
        """Create a simple microphone icon"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw microphone shape
        painter.setBrush(QColor(0, 213, 255))  # Cyan color
        painter.setPen(QColor(255, 255, 255, 200))
        
        # Mic body
        painter.drawRoundedRect(12, 8, 8, 12, 3, 3)
        
        # Mic stand
        painter.drawLine(16, 20, 16, 26)
        painter.drawLine(12, 26, 20, 26)
        
        # Sound waves
        painter.setPen(QColor(0, 213, 255, 150))
        painter.drawArc(6, 10, 8, 8, 0, 180 * 16)
        painter.drawArc(4, 8, 12, 12, 0, 180 * 16)
        
        painter.end()
        return QIcon(pixmap)
    
    def setup_menu(self):
        """Setup the context menu"""
        menu = QMenu()
        
        # Quick paste last transcription
        self.paste_last_action = QAction("📋 Paste Last", self)
        self.paste_last_action.triggered.connect(self.paste_last_transcription)
        menu.addAction(self.paste_last_action)
        
        menu.addSeparator()
        
        # History submenu
        self.history_menu = QMenu("📚 Recent History", menu)
        menu.addMenu(self.history_menu)
        
        # Show full history
        show_history_action = QAction("📖 Show All History...", self)
        show_history_action.triggered.connect(self.show_history_requested.emit)
        menu.addAction(show_history_action)
        
        menu.addSeparator()
        
        # Toggle mic bar visibility
        self.toggle_visibility_action = QAction("👁️ Toggle Mic Bar", self)
        self.toggle_visibility_action.triggered.connect(self.toggle_visibility_requested.emit)
        menu.addAction(self.toggle_visibility_action)
        
        menu.addSeparator()
        
        # About
        about_action = QAction("ℹ️ About VoxVibe", self)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        # Quit
        quit_action = QAction("❌ Quit", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
        
        # Update history menu initially
        self.update_history_menu()
    
    def update_history_menu(self):
        """Update the recent history submenu"""
        self.history_menu.clear()
        
        # Get recent entries
        recent_entries = self.history.get_recent(limit=10)
        
        if not recent_entries:
            no_history_action = QAction("(No recent history)", self)
            no_history_action.setEnabled(False)
            self.history_menu.addAction(no_history_action)
            
            # Disable paste last action
            self.paste_last_action.setEnabled(False)
            self.paste_last_action.setText("📋 Paste Last (none)")
        else:
            # Enable paste last action
            self.paste_last_action.setEnabled(True)
            last_text = recent_entries[0].text
            preview = last_text[:30] + "..." if len(last_text) > 30 else last_text
            self.paste_last_action.setText(f"📋 Paste Last: \"{preview}\"")
            
            # Add recent entries to submenu
            for entry in recent_entries:
                # Create preview text
                preview = entry.text[:40] + "..." if len(entry.text) > 40 else entry.text
                timestamp = entry.timestamp.strftime("%H:%M")
                
                action_text = f"[{timestamp}] {preview}"
                action = QAction(action_text, self)
                action.triggered.connect(lambda checked, text=entry.text: self.paste_text(text))
                self.history_menu.addAction(action)
    
    def paste_last_transcription(self):
        """Paste the most recent transcription"""
        last_entry = self.history.get_last_entry()
        if last_entry:
            self.paste_text(last_entry.text)
        else:
            self.show_message("No History", "No recent transcriptions found.", QMessageBox.Icon.Information)
    
    def paste_text(self, text: str):
        """Paste text using the window manager"""
        if self.window_manager:
            try:
                # Store current window before pasting
                self.window_manager.store_current_window()
                success = self.window_manager.focus_and_paste(text)
                
                if success:
                    print(f"✅ Pasted from history: {text[:50]}...")
                    self.show_message("Pasted", f"Text pasted successfully!", 
                                    QMessageBox.Icon.Information, timeout=2000)
                else:
                    print(f"❌ Failed to paste from history")
                    self.show_message("Paste Failed", "Could not paste text. Try again.", 
                                    QMessageBox.Icon.Warning)
                    
            except Exception as e:
                print(f"❌ Error pasting from history: {e}")
                self.show_message("Error", f"Paste error: {e}", QMessageBox.Icon.Critical)
        else:
            # Fallback: emit signal for manual handling
            self.paste_requested.emit(text)
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double-click to paste last transcription
            self.paste_last_transcription()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            # Middle-click to toggle mic bar visibility
            self.toggle_visibility_requested.emit()
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(None, "About VoxVibe", 
                         "VoxVibe v0.2\n\n"
                         "Voice transcription with global hotkeys\n"
                         "and persistent floating mic bar.\n\n"
                         "Hotkeys:\n"
                         "• Alt+Space: Hold to talk\n"
                         "• Win+Alt: Hold to talk\n"
                         "• Win+Alt+Space: Hands-free mode\n"
                         "• Space: Exit hands-free mode")
    
    def show_message(self, title: str, message: str, icon=QMessageBox.Icon.Information, timeout: int = 5000):
        """Show a system tray message"""
        if self.supportsMessages():
            self.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, timeout)
        else:
            # Fallback to message box
            msg_box = QMessageBox()
            msg_box.setIcon(icon)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.exec()
    
    def update_status(self, recording: bool, mode: str = ""):
        """Update tray icon status based on recording state"""
        if recording:
            tooltip = f"VoxVibe - Recording ({mode})"
            # Could change icon color/style here
        else:
            tooltip = "VoxVibe - Ready"
        
        self.setToolTip(tooltip)
        
        # Update history menu when not recording (new entry might be available)
        if not recording:
            self.update_history_menu()
    
    def notify_transcription_complete(self, text: str):
        """Notify that a new transcription is complete"""
        preview = text[:50] + "..." if len(text) > 50 else text
        self.show_message("Transcription Complete", f'"{preview}"', timeout=3000)
        self.update_history_menu() 