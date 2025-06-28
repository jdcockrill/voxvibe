from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from .config import UIConfig


class SystemTrayIcon(QSystemTrayIcon):
    quit_requested = pyqtSignal()
    start_recording_requested = pyqtSignal()
    stop_recording_requested = pyqtSignal()
    toggle_recording_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    history_requested = pyqtSignal()

    def __init__(self, config: Optional[UIConfig] = None, parent=None, tooltip="VoxVibe Voice Dictation", service_mode=False):
        self.config = config or UIConfig()
        self.service_mode = service_mode
        self.recording_state = "idle"  # idle, recording, processing

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

        # Try to get system theme icon first
        icon_name = "audio-input-microphone" if state == "idle" else "microphone-sensitivity-high"
        icon = QIcon.fromTheme(icon_name)
        return icon

    def _add_actions(self):
        if self.service_mode:
            # Primary toggle action
            self.toggle_action = self._menu.addAction("Start Recording")
            self.toggle_action.triggered.connect(self._on_toggle_recording_requested)
            self._menu.addSeparator()

            settings_action = self._menu.addAction("Settings")
            history_action = self._menu.addAction("History")
            self._menu.addSeparator()

            settings_action.triggered.connect(self.settings_requested.emit)
            history_action.triggered.connect(self.history_requested.emit)

        quit_action = self._menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_requested.emit)

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
