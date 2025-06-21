"""Persistent floating microphone bar with live waveform visualization.

Provides a minimal, draggable UI that stays visible and shows recording status.
"""
import math
import time
from typing import List, Optional

from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QMouseEvent
from PyQt6.QtWidgets import QWidget, QApplication

from .hotkey_service import RecordingMode


class MicBar(QWidget):
    # Signals
    drag_started = pyqtSignal()
    drag_ended = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # State
        self.recording_mode = RecordingMode.IDLE
        self.is_recording = False
        self.audio_levels: List[float] = [0.0] * 5  # 5 bars
        self.max_level = 0.0
        
        # Drag state
        self.dragging = False
        self.drag_start_pos = QPoint()
        self.drag_start_window_pos = QPoint()
        
        # Animation
        self.pulse_animation = QPropertyAnimation(self, b"windowOpacity")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        
        # Timers
        self.waveform_timer = QTimer()
        self.waveform_timer.timeout.connect(self.update_waveform)
        self.waveform_timer.start(50)  # 20 FPS
        
        self.decay_timer = QTimer()
        self.decay_timer.timeout.connect(self.decay_levels)
        self.decay_timer.start(100)  # 10 FPS
        
        self.setup_ui()
        self.position_widget()
    
    def setup_ui(self):
        """Setup the widget appearance and behavior"""
        # Window flags for floating behavior
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        
        # Make it semi-transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Set fixed size
        self.setFixedSize(120, 40)
        
        # Set window title for debugging
        self.setWindowTitle("VoxVibe Mic Bar")
        
        # Initial opacity
        self.setWindowOpacity(0.8)
    
    def position_widget(self):
        """Position the widget at the bottom center of the screen"""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # Position above the dock/taskbar
        x = (screen_geometry.width() - self.width()) // 2
        y = screen_geometry.height() - self.height() - 60  # 60px from bottom
        
        self.move(x, y)
    
    def set_recording_mode(self, mode: RecordingMode):
        """Update the recording mode and visual state"""
        self.recording_mode = mode
        self.is_recording = mode in [RecordingMode.HOLD_TO_TALK, RecordingMode.HANDS_FREE]
        
        # Skip opacity changes that cause Wayland issues
        # if self.is_recording:
        #     self.setWindowOpacity(1.0)
        #     self.pulse_animation.stop()
        # else:
        #     self.setWindowOpacity(0.6)
        #     if mode == RecordingMode.IDLE:
        #         self.start_idle_pulse()
        
        self.update()
    
    def start_idle_pulse(self):
        """Start subtle pulsing animation when idle"""
        # Disable pulsing animation to avoid opacity issues
        # self.pulse_animation.setStartValue(0.4)
        # self.pulse_animation.setEndValue(0.8)
        # self.pulse_animation.setLoopCount(-1)  # Infinite loop
        # self.pulse_animation.start()
        pass
    
    def update_audio_level(self, level: float):
        """Update the audio level for waveform visualization
        
        Args:
            level: Audio level between 0.0 and 1.0
        """
        if not self.is_recording:
            return
            
        # Update max level
        self.max_level = max(self.max_level, level)
        
        # Add some randomness to make it look more natural
        import random
        for i in range(len(self.audio_levels)):
            # Each bar responds slightly differently
            bar_sensitivity = 0.7 + (i * 0.1)  # Bars get more sensitive
            noise = random.uniform(-0.05, 0.05)
            self.audio_levels[i] = min(1.0, max(0.0, level * bar_sensitivity + noise))
    
    def update_waveform(self):
        """Update waveform animation"""
        if self.is_recording:
            # Simulate some movement even without real audio
            import random
            base_level = random.uniform(0.1, 0.3)
            for i in range(len(self.audio_levels)):
                self.audio_levels[i] = base_level + random.uniform(-0.1, 0.1)
        
        self.update()
    
    def decay_levels(self):
        """Gradually decay audio levels when not receiving input"""
        decay_rate = 0.85
        for i in range(len(self.audio_levels)):
            self.audio_levels[i] *= decay_rate
        
        self.max_level *= decay_rate
    
    def paintEvent(self, event):
        """Custom paint event for the mic bar"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Colors based on recording state
        if self.is_recording:
            if self.recording_mode == RecordingMode.HANDS_FREE:
                bg_color = QColor(255, 83, 255, 180)  # Magenta for hands-free
                bar_color = QColor(255, 255, 255, 220)
            else:
                bg_color = QColor(0, 213, 255, 180)  # Cyan for hold-to-talk
                bar_color = QColor(255, 255, 255, 220)
        else:
            bg_color = QColor(27, 29, 43, 120)  # Dark navy (idle)
            bar_color = QColor(230, 230, 230, 100)
        
        # Draw background capsule
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)
        
        # Draw waveform bars
        if self.is_recording or any(level > 0.01 for level in self.audio_levels):
            self.draw_waveform(painter, bar_color)
        else:
            self.draw_microphone_icon(painter)
    
    def draw_waveform(self, painter: QPainter, color: QColor):
        """Draw the waveform visualization"""
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Calculate bar dimensions
        bar_width = 4
        bar_spacing = 6
        max_bar_height = 20
        start_x = (self.width() - (len(self.audio_levels) * bar_spacing - 2)) // 2
        base_y = self.height() // 2
        
        # Draw bars
        for i, level in enumerate(self.audio_levels):
            bar_height = max(2, int(level * max_bar_height))
            x = start_x + i * bar_spacing
            y = base_y - bar_height // 2
            
            painter.drawRoundedRect(x, y, bar_width, bar_height, 2, 2)
    
    def draw_microphone_icon(self, painter: QPainter):
        """Draw a simple microphone icon when idle"""
        painter.setPen(QPen(QColor(230, 230, 230, 150), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Simple mic icon
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Mic body (rounded rectangle)
        painter.drawRoundedRect(center_x - 6, center_y - 8, 12, 16, 4, 4)
        
        # Mic stand
        painter.drawLine(center_x, center_y + 8, center_x, center_y + 12)
        painter.drawLine(center_x - 4, center_y + 12, center_x + 4, center_y + 12)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"🖱️ Mouse pressed on MicBar at local pos: ({event.position().x():.1f}, {event.position().y():.1f})")
            print(f"🖱️ Mouse pressed on MicBar at global pos: ({event.globalPosition().x():.1f}, {event.globalPosition().y():.1f})")
            
            self.dragging = True
            self.drag_start_pos = event.globalPosition().toPoint()
            self.drag_start_window_pos = self.pos()
            self.drag_started.emit()
            
            print(f"🖱️ Started dragging MicBar from window pos: ({self.drag_start_window_pos.x()}, {self.drag_start_window_pos.y()})")
            
            # Stop pulsing while dragging
            self.pulse_animation.stop()
            self.setWindowOpacity(1.0)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for dragging"""
        if self.dragging:
            delta = event.globalPosition().toPoint() - self.drag_start_pos
            new_pos = self.drag_start_window_pos + delta
            print(f"🖱️ Dragging MicBar to: ({new_pos.x()}, {new_pos.y()}) (delta: {delta.x()}, {delta.y()})")
            self.move(new_pos)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to end dragging"""
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            final_pos = self.pos()
            print(f"🖱️ Mouse released on MicBar at global pos: ({event.globalPosition().x():.1f}, {event.globalPosition().y():.1f})")
            print(f"🖱️ Finished dragging MicBar to final pos: ({final_pos.x()}, {final_pos.y()})")
            
            self.dragging = False
            self.drag_ended.emit()
            
            # Resume normal opacity behavior
            if not self.is_recording:
                self.start_idle_pulse()
    
    def show_temporarily(self, duration_ms: int = 2000):
        """Show the bar temporarily with full opacity"""
        self.pulse_animation.stop()
        self.setWindowOpacity(1.0)
        self.show()
        
        # Return to normal state after duration
        QTimer.singleShot(duration_ms, self.return_to_normal_state)
    
    def return_to_normal_state(self):
        """Return to normal opacity/animation state"""
        if not self.is_recording:
            self.start_idle_pulse()
    
    def set_visible_persistent(self, visible: bool):
        """Set persistent visibility (can be toggled in settings)"""
        if visible:
            self.show()
        else:
            self.hide() 