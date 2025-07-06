"""Window manager package with pluggable strategies for different desktop environments."""

from .base import WindowManagerStrategy
from .dbus_strategy import DBusWindowManagerStrategy
from .manager import WindowManager

__all__ = ["WindowManager", "WindowManagerStrategy", "DBusWindowManagerStrategy"]
