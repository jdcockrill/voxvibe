import logging
import threading
from typing import Callable, Optional

import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class KeyboardHotkeyManager(QObject):
    """Alternative hotkey manager using keyboard library for better Linux browser support"""
    
    hotkey_pressed = pyqtSignal()
    
    def __init__(self, hotkey: str = "ctrl+shift+space"):
        super().__init__()
        self.hotkey = hotkey
        self._is_active = False
        self._hotkey_callback = None
        
    def start(self) -> bool:
        """Start listening for global hotkeys using keyboard library"""
        if self._is_active:
            logger.warning("Keyboard hotkey manager already active")
            return True
            
        try:
            # Register hotkey using keyboard library
            keyboard.add_hotkey(self.hotkey, self._on_hotkey_pressed)
            self._is_active = True
            
            logger.info(f"Global hotkey registered with keyboard library: {self.hotkey}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register global hotkey '{self.hotkey}' with keyboard library: {e}")
            return False
    
    def stop(self):
        """Stop listening for global hotkeys"""
        if not self._is_active:
            return
            
        try:
            # Remove the specific hotkey
            keyboard.remove_hotkey(self.hotkey)
            self._is_active = False
            logger.info("Keyboard hotkey listener stopped")
            
        except Exception as e:
            logger.error(f"Error stopping keyboard hotkey listener: {e}")
    
    def _on_hotkey_pressed(self):
        """Internal callback when hotkey is detected"""
        logger.debug(f"Global hotkey pressed with keyboard library: {self.hotkey}")
        # Emit signal in thread-safe way
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