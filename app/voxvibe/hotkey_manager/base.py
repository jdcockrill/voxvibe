from abc import abstractmethod

from PyQt6.QtCore import QObject, pyqtSignal


class AbstractHotkeyManager(QObject):
    hotkey_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()

    def start(self) -> bool:
        raise NotImplementedError("Subclasses must implement start()")

    def stop(self) -> None:
        raise NotImplementedError("Subclasses must implement stop()")

    def is_active(self) -> bool:
        raise NotImplementedError("Subclasses must implement is_active()")
