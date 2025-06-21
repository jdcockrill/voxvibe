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
    args = parser.parse_args()


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

            sys.exit(app.exec())
    except SingleInstanceError as e:
        logging.error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
