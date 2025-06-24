import logging
from typing import Callable, Optional

from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class HotkeyManager(QObject):
    """Handles global hotkey registration and detection for VoxVibe service"""
    
    hotkey_pressed = pyqtSignal()
    
    def __init__(self, hotkey: str = "ctrl+alt+v"):
        super().__init__()
        self.hotkey = hotkey
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self._is_active = False
    
    def start(self) -> bool:
        """Start listening for global hotkeys"""
        if self._is_active:
            logger.warning("Hotkey manager already active")
            return True
            
        try:
            # Parse hotkey string into pynput format
            hotkey_combination = self._parse_hotkey(self.hotkey)
            
            # Create global hotkey listener
            self.listener = keyboard.GlobalHotKeys({
                hotkey_combination: self._on_hotkey_pressed
            })
            
            self.listener.start()
            self._is_active = True
            
            logger.info(f"Global hotkey registered: {self.hotkey}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register global hotkey '{self.hotkey}': {e}")
            return False
    
    def stop(self):
        """Stop listening for global hotkeys"""
        if not self._is_active:
            return
            
        try:
            if self.listener:
                self.listener.stop()
                self.listener = None
            
            self._is_active = False
            logger.info("Global hotkey listener stopped")
            
        except Exception as e:
            logger.error(f"Error stopping hotkey listener: {e}")
    
    def _parse_hotkey(self, hotkey_str: str) -> str:
        """Parse hotkey string and convert to pynput format"""
        # Convert common format to pynput format
        # Examples: "ctrl+alt+v" -> "<ctrl>+<alt>+v"
        parts = hotkey_str.lower().split('+')
        formatted_parts = []
        
        for part in parts:
            part = part.strip()
            if part in ['ctrl', 'alt', 'shift', 'cmd', 'super']:
                formatted_parts.append(f'<{part}>')
            else:
                # Regular key
                formatted_parts.append(part)
        
        return '+'.join(formatted_parts)
    
    def _on_hotkey_pressed(self):
        """Internal callback when hotkey is detected"""
        logger.debug(f"Global hotkey pressed: {self.hotkey}")
        self.hotkey_pressed.emit()
    
    def set_hotkey(self, hotkey: str) -> bool:
        """Change the global hotkey"""
        old_hotkey = self.hotkey
        was_active = self._is_active
        
        # Stop current listener
        if was_active:
            self.stop()
        
        # Update hotkey
        self.hotkey = hotkey
        
        # Restart if it was active
        if was_active:
            success = self.start()
            if not success:
                # Rollback on failure
                self.hotkey = old_hotkey
                self.start()
                return False
        
        logger.info(f"Hotkey changed from '{old_hotkey}' to '{hotkey}'")
        return True
    
    @property
    def is_active(self) -> bool:
        """Check if hotkey manager is currently active"""
        return self._is_active