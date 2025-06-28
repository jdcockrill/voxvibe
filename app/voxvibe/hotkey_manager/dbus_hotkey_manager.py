import logging
from typing import Optional

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtDBus import QDBusConnection

from ..config import HotkeyConfig
from .base import AbstractHotkeyManager

logger = logging.getLogger(__name__)

DBUS_SERVICE = "app.voxvibe.Service"
DBUS_OBJECT_PATH = "/app/voxvibe/Service"
DBUS_INTERFACE = "app.voxvibe.Service"


class DBusHotkeyManager(AbstractHotkeyManager):
    """Hotkey manager that exposes a DBus method for triggering the hotkey from external apps/extensions."""

    def __init__(self, config: Optional[HotkeyConfig] = None):
        super().__init__(config)
        self._is_active = False
        self._bus: Optional[QDBusConnection] = None

    @pyqtSlot()
    def TriggerHotkey(self):
        logger.info("DBus: TriggerHotkey called")
        self._on_hotkey_triggered_via_dbus()

    def start(self) -> bool:
        if self._is_active:
            logger.warning("Hotkey manager already active")
            return True
        try:
            self._bus = QDBusConnection.sessionBus()

            # Register the object and explicitly set the interface name so that
            # consumers (e.g. the GNOME Shell extension) can use the expected
            # `app.voxvibe.Service` interface instead of the automatically
            # generated `local.DBusHotkeyManager`.
            if not self._bus.registerObject(
                DBUS_OBJECT_PATH,
                DBUS_INTERFACE,
                self,
                QDBusConnection.RegisterOption.ExportAllSlots,
            ):
                logger.error("Failed to register DBus object path")
                return False

            if not self._bus.registerService(DBUS_SERVICE):
                logger.error("Failed to acquire DBus service name")
                self._bus.unregisterObject(DBUS_OBJECT_PATH)
                return False

            logger.info("Registered DBus hotkey service: %s at %s", DBUS_SERVICE, DBUS_OBJECT_PATH)
            self._is_active = True
            return True
        except Exception:
            logger.exception("Error setting up DBus hotkey service")
            return False

    def stop(self) -> None:
        try:
            if self._bus:
                self._bus.unregisterObject(DBUS_OBJECT_PATH)
                self._bus.unregisterService(DBUS_SERVICE)
                self._bus = None
        except Exception:
            logger.exception("Error stopping DBus hotkey manager")
        self._is_active = False

    def is_active(self) -> bool:
        return self._is_active

    def _on_hotkey_triggered_via_dbus(self):
        logger.info("Hotkey triggered via DBus!")
        self.hotkey_pressed.emit()
