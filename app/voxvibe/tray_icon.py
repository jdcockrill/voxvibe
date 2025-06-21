"""System tray icon for VoxVibe with history access and quick actions."""

import sys
from datetime import datetime, timezone
from typing import Optional
import os

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QCursor
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QMessageBox

from .history import TranscriptionHistory, HistoryEntry
from .window_manager import WindowManager


class VoxVibeTrayIcon(QSystemTrayIcon):
    # Signals
    paste_requested = pyqtSignal(str)  # text to paste
    quit_requested = pyqtSignal()
    
    def __init__(self, history: TranscriptionHistory, window_manager: Optional[WindowManager] = None):
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
        self.menu = QMenu()
        
        # Add label for history section (no separate paste last action)
        history_label = QAction("📚 Paste from History:", self)
        history_label.setEnabled(False)
        self.menu.addAction(history_label)
        
        # History items will be added here dynamically
        self.history_actions = []
        self.next_10_submenu = None
        
        self.menu.addSeparator()
        
        # About
        about_action = QAction("ℹ️ About VoxVibe", self)
        about_action.triggered.connect(self.show_about)
        self.menu.addAction(about_action)
        
        # Quit
        quit_action = QAction("❌ Quit", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(quit_action)
        
        self.setContextMenu(self.menu)
        
        # Update history menu initially
        self.update_history_menu()
    
    def update_history_menu(self):
        """Update the recent history items in main menu with Next 10 submenu"""
        # Remove existing history actions
        for action in self.history_actions:
            self.menu.removeAction(action)
        self.history_actions.clear()
        
        # Remove existing submenu if it exists
        if self.next_10_submenu:
            self.menu.removeAction(self.next_10_submenu.menuAction())
            self.next_10_submenu = None
        
        # Get recent entries (get 15 total: 5 in main menu + 10 in submenu)
        recent_entries = self.history.get_recent(limit=15)
        
        if not recent_entries:
            no_history_action = QAction("  (No recent history)", self)
            no_history_action.setEnabled(False)
            self.menu.insertAction(self.menu.actions()[-2], no_history_action)  # Insert before separator
            self.history_actions.append(no_history_action)
        else:
            # Add first 5 entries directly to main menu
            first_5 = recent_entries[:5]
            for i, entry in enumerate(first_5):
                # Create preview text
                preview = entry.text[:40] + "..." if len(entry.text) > 40 else entry.text
                # Convert UTC timestamp to local time (BST/GMT) for display
                local_time = self._convert_to_local_time(entry.timestamp)
                timestamp = local_time.strftime("%H:%M")
                
                if i == 0:
                    # First item is marked as "Last" and styled differently
                    action_text = f"  ★ Last - {timestamp}: {preview}"
                    action = QAction(action_text, self)
                    # Make it bold to stand out
                    font = action.font()
                    font.setBold(True)
                    action.setFont(font)
                else:
                    # Regular formatting for other items
                    action_text = f"  [{timestamp}] {preview}"
                    action = QAction(action_text, self)
                
                # Fix the clicking issue by creating a proper slot function
                def create_paste_slot(text):
                    return lambda: self.paste_text(text)
                
                action.triggered.connect(create_paste_slot(entry.text))
                self.menu.insertAction(self.menu.actions()[-2], action)  # Insert before separator
                self.history_actions.append(action)
            
            # Add "Next 10" submenu if there are more than 5 items
            if len(recent_entries) > 5:
                self.next_10_submenu = QMenu("📂 Next 10", self.menu)
                
                # Add entries 6-15 to submenu
                next_10 = recent_entries[5:]
                for entry in next_10:
                    # Create preview text
                    preview = entry.text[:40] + "..." if len(entry.text) > 40 else entry.text
                    # Convert UTC timestamp to local time (BST/GMT) for display
                    local_time = self._convert_to_local_time(entry.timestamp)
                    timestamp = local_time.strftime("%H:%M")
                    
                    action_text = f"[{timestamp}] {preview}"
                    action = QAction(action_text, self.next_10_submenu)
                    
                    # Fix the clicking issue by creating a proper slot function
                    def create_paste_slot(text):
                        return lambda: self.paste_text(text)
                    
                    action.triggered.connect(create_paste_slot(entry.text))
                    self.next_10_submenu.addAction(action)
                
                # Add submenu to main menu
                self.menu.insertMenu(self.menu.actions()[-2], self.next_10_submenu)
    
    def paste_text(self, text: str):
        """Paste text using the window manager"""
        if self.window_manager:
            try:
                # Store current window before pasting
                self.window_manager.store_current_window()
                
                # Set text to clipboard
                from PyQt6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                
                # Focus previous window and paste
                success = self.window_manager.paste_to_previous_window()
                
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
            last_entry = self.history.get_last_entry()
            if last_entry:
                self.paste_text(last_entry.text)
            else:
                self.show_message("No History", "No recent transcriptions found.", QMessageBox.Icon.Information)
    
    def show_about(self):
        """Show about dialog centered on screen"""
        # Create message box
        msg_box = QMessageBox()
        msg_box.setWindowTitle("About VoxVibe")
        msg_box.setText("VoxVibe v0.2.0\n\n"
                       "Voice transcription with global hotkeys.\n"
                       "Fast, reliable speech-to-text for Linux.\n\n"
                       "Hotkeys:\n"
                       "• Win+Alt: Hold to talk\n\n"
                       "Features:\n"
                       "• Ultra-fast pasting (0.25s)\n"
                       "• History access via tray menu\n"
                       "• Native Wayland support")
        msg_box.setIcon(QMessageBox.Icon.Information)
        
        # Center the dialog on screen
        try:
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.availableGeometry()
                screen_center_x = screen_geometry.width() // 2
                screen_center_y = screen_geometry.height() // 2
                
                # Position dialog at screen center (dialog will auto-size, so we just set position)
                dialog_x = screen_center_x - 200  # Rough estimate for half dialog width
                dialog_y = screen_center_y - 150  # Rough estimate for half dialog height
                
                msg_box.move(dialog_x, dialog_y)
                print(f"📱 About dialog centered on screen at ({dialog_x}, {dialog_y})")
            else:
                print("📱 No screen found, using default dialog position")
        except Exception as e:
            print(f"📱 Could not center dialog: {e}")
            # Will use default positioning as fallback
        
        msg_box.exec()
    
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
    
    def _convert_to_local_time(self, utc_datetime: datetime) -> datetime:
        """Convert UTC datetime to local system time (handles BST/GMT automatically)"""
        # If the datetime is naive (no timezone info), assume it's UTC
        if utc_datetime.tzinfo is None:
            utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
        
        # Convert to local timezone
        local_datetime = utc_datetime.astimezone()
        return local_datetime

    def notify_transcription_complete(self, text: str):
        """Notify that a new transcription is complete"""
        preview = text[:50] + "..." if len(text) > 50 else text
        self.show_message("Transcription Complete", f'"{preview}"', timeout=3000)
        self.update_history_menu() 