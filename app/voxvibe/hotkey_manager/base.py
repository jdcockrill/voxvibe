
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from ..config import HotkeyConfig


class AbstractHotkeyManager(QObject):
    hotkey_pressed = pyqtSignal()

    def __init__(self, config: Optional[HotkeyConfig] = None):
        super().__init__()
        self.config = config or HotkeyConfig()

    def start(self) -> bool:
        raise NotImplementedError("Subclasses must implement start()")

    def stop(self) -> None:
        raise NotImplementedError("Subclasses must implement stop()")

    def is_active(self) -> bool:
        raise NotImplementedError("Subclasses must implement is_active()")
