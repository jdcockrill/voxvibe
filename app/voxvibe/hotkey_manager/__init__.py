import logging
from typing import Optional

from ..config import HotkeyConfig
from .base import AbstractHotkeyManager
from .dbus_hotkey_manager import DBusHotkeyManager
from .qt_hotkey_manager import QtHotkeyManager

logger = logging.getLogger(__name__)


def create_hotkey_manager(config: Optional[HotkeyConfig] = None) -> AbstractHotkeyManager:
    """Create a hotkey manager based on configuration.
    
    Args:
        config: HotkeyConfig object with strategy preferences
        
    Returns:
        AbstractHotkeyManager instance
    """
    if config is None:
        config = HotkeyConfig()
    
    strategy = config.strategy
    
    if strategy == "qt":
        return QtHotkeyManager(config)
    elif strategy == "dbus":
        return DBusHotkeyManager(config)
    elif strategy == "auto":
        # Default to DBus for auto
        return DBusHotkeyManager(config)
    else:
        logger.warning(f"Unknown hotkey strategy: {strategy}, using dbus")
        return DBusHotkeyManager(config)


__all__ = [
    "AbstractHotkeyManager",
    "QtHotkeyManager",
    "DBusHotkeyManager",
    "create_hotkey_manager",
]
