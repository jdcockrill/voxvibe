"""GNOME Shell DBus client used to store the currently focused window and
focus & paste text via the Voice-Flow GNOME extension.

Exposes a small API used by the Qt application:

    wm = DBusWindowManager()
    wm.store_current_window()
    success = wm.focus_and_paste(text)

Requires PyQt6.QtDBus to be available.
"""
from __future__ import annotations

from typing import Optional
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage

_BUS_NAME = "org.gnome.Shell"  # GNOME Shell owns this name
_OBJECT_PATH = "/org/gnome/Shell/Extensions/VoxVibe"
_INTERFACE = "org.gnome.Shell.Extensions.VoxVibe"


class DBusWindowManager:
    """Lightweight wrapper around the GNOME extension DBus interface."""

    def __init__(self) -> None:
        self._bus = QDBusConnection.sessionBus()
        if not self._bus.isConnected():
            raise RuntimeError("Cannot connect to the session DBus bus")

        self._interface = QDBusInterface(_BUS_NAME, _OBJECT_PATH, _INTERFACE, self._bus)
        if not self._interface.isValid():
            raise RuntimeError("Voice-Flow GNOME extension DBus interface not available. Is the extension enabled?")

        self._stored_window_id: Optional[str] = None

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def store_current_window(self) -> None:
        """Query GNOME Shell for the current focused window and remember its ID."""
        reply = self._interface.call("GetFocusedWindow")
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            raise RuntimeError(f"GetFocusedWindow DBus error: {reply.errorMessage()}")

        window_id = reply.arguments()[0] if reply.arguments() else ""
        if window_id:
            self._stored_window_id = str(window_id)
        else:
            self._stored_window_id = None

    def focus_and_paste(self, text: str) -> bool:
        """Focus previously stored window and paste *text* into it via DBus.

        Returns True on success, False otherwise.
        """
        if not self._stored_window_id:
            print("[DBusWindowManager] No stored window_id; cannot focus & paste")
            return False

        reply = self._interface.call("FocusAndPaste", self._stored_window_id, text)
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            print(f"[DBusWindowManager] FocusAndPaste error: {reply.errorMessage()}")
            return False

        return bool(reply.arguments()[0]) if reply.arguments() else False

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def check_extension_available(self) -> bool:
        """Return True if the GNOME extension interface can be reached."""
        return self._interface.isValid()
