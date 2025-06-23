import logging

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class SystemTrayIcon(QSystemTrayIcon):
    quit_requested = pyqtSignal()
    start_recording_requested = pyqtSignal()
    stop_recording_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    history_requested = pyqtSignal()

    def __init__(self, parent=None, tooltip="VoxVibe Voice Dictation", service_mode=False):
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
        icon_name = "microphone" if state == "idle" else "microphone-sensitivity-high"
        icon = QIcon.fromTheme(icon_name)
        
        if icon.isNull():
            try:
                from PyQt6.QtGui import QColor, QPainter, QPixmap
                pm = QPixmap(64, 64)
                pm.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pm)
                font = QFont()
                font.setPointSize(32)
                painter.setFont(font)
                
                # Different colors for different states
                if state == "recording":
                    painter.setPen(QColor(255, 0, 0))  # Red for recording
                    painter.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "🔴")
                elif state == "processing":
                    painter.setPen(QColor(255, 165, 0))  # Orange for processing
                    painter.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "⚙️")
                else:
                    painter.setPen(QColor(0, 0, 0))  # Black for idle
                    painter.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "🎤")
                    
                painter.end()
                icon = QIcon(pm)
            except Exception:
                icon = QIcon()
        return icon

    def _add_actions(self):
        if self.service_mode:
            self.start_action = self._menu.addAction("Start Recording")
            self.stop_action = self._menu.addAction("Stop Recording")
            self.stop_action.setEnabled(False)  # Disabled initially
            self._menu.addSeparator()
            
            settings_action = self._menu.addAction("Settings")
            history_action = self._menu.addAction("History")
            self._menu.addSeparator()
            
            self.start_action.triggered.connect(self.start_recording_requested.emit)
            self.stop_action.triggered.connect(self.stop_recording_requested.emit)
            settings_action.triggered.connect(self.settings_requested.emit)
            history_action.triggered.connect(self.history_requested.emit)
            
        quit_action = self._menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_requested.emit)

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
            self.start_action.setEnabled(state == "idle")
            self.stop_action.setEnabled(state == "recording")

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.service_mode:
                # In service mode, single click toggles recording
                if self.recording_state == "idle":
                    self.start_recording_requested.emit()
                elif self.recording_state == "recording":
                    self.stop_recording_requested.emit()
