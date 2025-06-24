"""Window manager package with pluggable strategies for different desktop environments."""

from .base import WindowManagerStrategy
from .dbus_strategy import DBusWindowManagerStrategy
from .manager import WindowManager
from .xdotool_strategy import XdotoolWindowManagerStrategy

__all__ = [
    'WindowManager',
    'WindowManagerStrategy', 
    'DBusWindowManagerStrategy',
    'XdotoolWindowManagerStrategy'
]