from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .config import UIConfig


class SystemTrayIcon(QSystemTrayIcon):
    quit_requested = pyqtSignal()
    start_recording_requested = pyqtSignal()
    stop_recording_requested = pyqtSignal()
    toggle_recording_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    history_requested = pyqtSignal()
    history_copy_requested = pyqtSignal(str)  # Signal with text to copy

    def __init__(self, config: Optional[UIConfig] = None, parent=None, tooltip="VoxVibe Voice Dictation", service_mode=False):
        self.config = config or UIConfig()
        self.service_mode = service_mode
        self.recording_state = "idle"  # idle, recording, processing
        self.history_entries = []  # Store history entries for menu

        icon = self._create_icon()
        super().__init__(icon, parent)
        self.setToolTip(tooltip)
        self._menu = QMenu()
        self._add_actions()
        self.setContextMenu(self._menu)
        self.activated.connect(self._on_activated)

    def _create_icon(self, state=None):
        if state is None:
            state = self.recording_state

        # Get the icons directory path
        icons_dir = Path(__file__).parent / "icons"
        
        # Map states to icon files
        icon_files = {
            "idle": "idle.png",
            "recording": "recording.png", 
            "processing": "processing.png"
        }
        
        # Get the appropriate icon file
        icon_file = icon_files.get(state, "idle.png")
        icon_path = icons_dir / icon_file
        
        # Load custom icon if it exists, otherwise fallback to theme icon
        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            # Fallback to system theme icons
            icon_name = "audio-input-microphone" if state == "idle" else "microphone-sensitivity-high"
            icon = QIcon.fromTheme(icon_name)
        
        return icon

    def _add_actions(self):
        if self.service_mode:
            # Primary toggle action
            self.toggle_action = self._menu.addAction("Start Recording")
            self.toggle_action.triggered.connect(self._on_toggle_recording_requested)
            self._menu.addSeparator()

            # Add history section
            self._add_history_section()
            
            settings_action = self._menu.addAction("Settings")
            self._menu.addSeparator()

            settings_action.triggered.connect(self.settings_requested.emit)

        quit_action = self._menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_requested.emit)

    def _add_history_section(self):
        """Add history items to the menu"""
        if not self.history_entries:
            # Show placeholder when no history
            no_history_action = self._menu.addAction("No transcription history")
            no_history_action.setEnabled(False)
            self._menu.addSeparator()
            return

        # Add last 3 items directly to menu
        recent_entries = self.history_entries[:3]
        for entry in recent_entries:
            display_text = self._truncate_text(entry.text, 40)
            action = self._menu.addAction(f"📋 {display_text}")
            action.triggered.connect(lambda checked, text=entry.text: self._copy_to_clipboard(text))

        # Add "More >" submenu if there are more than 3 entries
        if len(self.history_entries) > 3:
            more_entries = self.history_entries[3:13]  # Next 10 items
            if more_entries:
                more_menu = QMenu("More", self._menu)
                for entry in more_entries:
                    display_text = self._truncate_text(entry.text, 50)
                    action = more_menu.addAction(f"📋 {display_text}")
                    action.triggered.connect(lambda checked, text=entry.text: self._copy_to_clipboard(text))
                self._menu.addMenu(more_menu)

        self._menu.addSeparator()

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text for display in menu items"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    def _copy_to_clipboard(self, text: str):
        """Copy text to system clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.history_copy_requested.emit(text)

    def update_history(self, history_entries: List):
        """Update the history entries and rebuild the menu"""
        self.history_entries = history_entries
        self._rebuild_menu()

    def _rebuild_menu(self):
        """Rebuild the entire menu with updated history"""
        self._menu.clear()
        self._add_actions()

    def _on_toggle_recording_requested(self):
        if self.toggle_action.text() == "Start Recording":
            self.toggle_action.setText("Stop Recording")
        else:
            self.toggle_action.setText("Start Recording")
        self.toggle_recording_requested.emit()

    def set_recording_state(self, state):
        """Update the recording state and icon"""
        if state not in ["idle", "recording", "processing"]:
            return

        self.recording_state = state
        self.setIcon(self._create_icon(state))

        # Update tooltip
        if state == "recording":
            self.setToolTip("VoxVibe - Recording...")
        elif state == "processing":
            self.setToolTip("VoxVibe - Processing...")
        else:
            self.setToolTip("VoxVibe - Ready")

        # Update menu actions if in service mode
        if self.service_mode:
            # Update toggle action text based on state
            if state == "idle":
                self.toggle_action.setText("Start Recording")
            elif state == "recording":
                self.toggle_action.setText("Stop Recording")
            else:  # processing
                self.toggle_action.setText("Processing...")
            self.toggle_action.setEnabled(state in ["idle", "recording"])

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.service_mode:
                # In service mode, single click toggles recording
                self.toggle_recording_requested.emit()
