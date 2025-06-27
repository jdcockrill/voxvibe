import logging
from typing import Optional

from pynput import keyboard
from PyQt6.QtCore import pyqtSignal

from .base import AbstractHotkeyManager

logger = logging.getLogger(__name__)


class QtHotkeyManager(AbstractHotkeyManager):
    """Handles global hotkey registration and detection for VoxVibe service using pynput."""

    def __init__(self, hotkey: str = "<super>x"):
        super().__init__()
        self.hotkey = hotkey
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self._is_active = False

    def start(self) -> bool:
        if self._is_active:
            logger.warning("Hotkey manager already active")
            return True
        try:
            self.listener = keyboard.GlobalHotKeys({self.hotkey: self._on_hotkey_pressed})
            self.listener.start()
            self._is_active = True
            logger.info(f"Global hotkey registered: {self.hotkey}")
            return True
        except Exception as e:
            logger.error(f"Failed to register global hotkey '{self.hotkey}': {e}")
            return False

    def stop(self) -> None:
        if self.listener:
            try:
                self.listener.stop()
                self._is_active = False
                logger.info("Global hotkey listener stopped")
            except Exception as e:
                logger.error(f"Error stopping hotkey listener: {e}")

    def is_active(self) -> bool:
        return self._is_active

    def _on_hotkey_pressed(self):
        logger.debug(f"Global hotkey pressed: {self.hotkey}")
        self.hotkey_pressed.emit()
