#!/usr/bin/env python3
import argparse
import logging
import signal
import sys

from PyQt6.QtWidgets import QApplication

from .dbus_window_manager import DBusWindowManager
from .single_instance import SingleInstance, SingleInstanceError
from .theme import apply_theme
from .ui import DictationApp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--reset", action="store_true", help="Clear any stale single-instance lock and exit")
    parser.add_argument("--service", action="store_true", help="Run as background service with system tray")
    args = parser.parse_args()

    if args.service:
        return run_service_mode(args)
    else:
        return run_normal_mode(args)


def run_service_mode(args):
    """Run VoxVibe as a background service with system tray"""
    from .service import VoxVibeService
    
    # Different single-instance lock for service mode
    try:
        with SingleInstance("voxvibe_service_instance", reset=args.reset):
            if args.reset:
                logging.info("Service single-instance lock reset successfully.")
                return 0

            app = QApplication(sys.argv)
            app.setQuitOnLastWindowClosed(False)  # Don't quit when windows are closed
            app.setApplicationName("VoxVibe Service")
            apply_theme(app)

            # Check if system tray is available
            from PyQt6.QtWidgets import QSystemTrayIcon
            if not QSystemTrayIcon.isSystemTrayAvailable():
                logging.error("System tray is not available on this system")
                return 1

            service = VoxVibeService(app)
            if not service.start():
                logging.error("Failed to start VoxVibe service")
                return 1

            logging.info("VoxVibe service started successfully")
            return app.exec()
            
    except SingleInstanceError as e:
        logging.error(e)
        return 1


def run_normal_mode(args):
    """Run VoxVibe in normal (original) mode"""
    # ------------------------------------------------------------------
    # Single-instance guard
    # ------------------------------------------------------------------
    # VoxVibe is usually launched via a global keyboard shortcut; pressing it
    # repeatedly can start multiple recorder windows that compete for the
    # microphone and clutter the desktop. To prevent this we acquire a
    # process-wide lock implemented in single_instance.py using QLocalServer.
    # If another VoxVibe instance is already running we exit immediately.
    # The optional `--reset` flag removes a stale lock left behind by a crash.
    try:
        with SingleInstance("voxvibe_single_instance", reset=args.reset):
            if args.reset:
                logging.info("Single-instance lock reset successfully.")
                return 0  # Exit immediately after reset

            # Handle Ctrl+C gracefully
            signal.signal(signal.SIGINT, signal.SIG_DFL)

            # Store the currently active window BEFORE creating the Qt app
            window_manager = DBusWindowManager()
            window_manager.store_current_window()

            app = QApplication(sys.argv)
            app.setQuitOnLastWindowClosed(True)
            app.setApplicationName("VoxVibe")
            apply_theme(app)

            window = DictationApp(window_manager)
            window.setWindowTitle("VoxVibe")
            window.show()

            return app.exec()
    except SingleInstanceError as e:
        logging.error(e)
        return 1


if __name__ == "__main__":
    main()
