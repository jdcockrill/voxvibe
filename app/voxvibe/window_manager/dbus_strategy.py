"""GNOME Shell DBus window manager strategy using VoxVibe extension."""

import json
import logging
from typing import Any, Dict, Optional

from PyQt6.QtCore import QVariant
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage

from .base import WindowManagerStrategy

logger = logging.getLogger(__name__)

_BUS_NAME = "org.gnome.Shell"  # GNOME Shell owns this name
_OBJECT_PATH = "/org/gnome/Shell/Extensions/VoxVibe"
_INTERFACE = "org.gnome.Shell.Extensions.VoxVibe"


class DBusWindowManagerStrategy(WindowManagerStrategy):
    """Window manager strategy using GNOME Shell DBus extension."""

    def __init__(self):
        self._bus = None
        self._interface = None
        self._stored_window_info: Optional[str] = None
        self._stored_window_id: Optional[int] = None
        self._initialized = False

    def _initialize(self) -> bool:
        """Initialize DBus connection if not already done."""
        if self._initialized:
            return self._interface is not None

        self._initialized = True

        try:
            self._bus = QDBusConnection.sessionBus()
            if not self._bus.isConnected():
                logger.error("Cannot connect to the session DBus bus")
                return False

            self._interface = QDBusInterface(_BUS_NAME, _OBJECT_PATH, _INTERFACE, self._bus)
            if not self._interface.isValid():
                logger.debug("VoxVibe GNOME extension DBus interface not available")
                return False

            logger.debug("DBus window manager strategy initialized successfully")
            return True

        except Exception as e:
            logger.debug(f"Failed to initialize DBus strategy: {e}")
            return False

    def is_available(self) -> bool:
        """Check if this strategy is available on the current system."""
        return self._initialize()

    def store_current_window(self) -> None:
        """Store information about the currently focused window."""
        if not self._initialize():
            raise RuntimeError("DBus strategy not available")

        reply = self._interface.call("GetFocusedWindow")
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            raise RuntimeError(f"GetFocusedWindow DBus error: {reply.errorMessage()}")

        window_info_json = reply.arguments()[0] if reply.arguments() else ""
        if window_info_json:
            self._stored_window_info = str(window_info_json)
            try:
                window_info = json.loads(window_info_json)
                self._stored_window_id = window_info["id"]
                logger.debug(f"Stored window info: {window_info['title']} (ID: {window_info['id']})")
            except json.JSONDecodeError:
                self._stored_window_id = None
                logger.debug(f"Stored window info: {self._stored_window_info}")
        else:
            self._stored_window_info = None
            self._stored_window_id = None
            logger.warning("No focused window found")

    def focus_and_paste(self, text: str) -> bool:
        """Focus the previously stored window and paste text into it.

        Args:
            text: The text to paste

        Returns:
            True if successful, False otherwise
        """
        if not self._initialize():
            raise RuntimeError("DBus strategy not available")

        if not self._stored_window_id:
            logger.warning("No stored window ID; cannot focus & paste")
            return False

        # Ensure window ID is sent as unsigned 32-bit integer
        window_id_unsigned = int(self._stored_window_id) & 0xFFFFFFFF
        reply = self._interface.call("FocusAndPaste", window_id_unsigned, text)
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            logger.error(f"FocusAndPaste error: {reply.errorMessage()}")
            return False

        result = bool(reply.arguments()[0]) if reply.arguments() else False
        if result:
            if self._stored_window_info:
                try:
                    window_info = json.loads(self._stored_window_info)
                    logger.debug(
                        f"Successfully pasted text to window: {window_info['title']} (ID: {window_info['id']})"
                    )
                except json.JSONDecodeError:
                    logger.debug(f"Successfully pasted text to window ID: {self._stored_window_id}")
            else:
                logger.debug(f"Successfully pasted text to window ID: {self._stored_window_id}")
        else:
            if self._stored_window_info:
                try:
                    window_info = json.loads(self._stored_window_info)
                    logger.warning(f"Failed to paste text to window: {window_info['title']} (ID: {window_info['id']})")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to paste text to window ID: {self._stored_window_id}")
            else:
                logger.warning(f"Failed to paste text to window ID: {self._stored_window_id}")

        return result

    def get_strategy_name(self) -> str:
        """Get a human-readable name for this strategy."""
        return "GNOME Shell DBus Extension"

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about this strategy."""
        base_diagnostics = super().get_diagnostics()

        # Add DBus-specific diagnostics
        dbus_diagnostics = {
            "bus_connected": self._bus.isConnected() if self._bus else False,
            "interface_valid": self._interface.isValid() if self._interface else False,
            "stored_window_info": self._stored_window_info,
            "stored_window_id": self._stored_window_id,
            "bus_name": _BUS_NAME,
            "object_path": _OBJECT_PATH,
            "interface_name": _INTERFACE,
        }

        base_diagnostics.update(dbus_diagnostics)
        return base_diagnostics

    def check_extension_available(self) -> bool:
        """Return True if the GNOME extension interface can be reached."""
        return self._initialize() and self._interface.isValid()
