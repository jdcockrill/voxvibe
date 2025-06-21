#!/usr/bin/env python3
import argparse
import logging
import signal
import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from .dbus_window_manager import DBusWindowManager
from .theme import apply_theme
from .ui import DictationApp
from .single_instance import SingleInstance, SingleInstanceError


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--reset", action="store_true", help="Clear any stale single-instance lock and exit")
    args, unknown = parser.parse_known_args()

    # Configure logging early
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        with SingleInstance("voxvibe_single_instance", reset=args.reset):
            if args.reset:
                logging.info("Single-instance lock reset successfully.")
                return 0  # Exit immediately after reset

            # Remove our custom flag from argv before passing to Qt
            if args.reset:
                sys.argv.remove("--reset")
            # Append unknown back to sys.argv to preserve e.g. -style args
            if unknown:
                # keep script path and add unknown args
                sys.argv = [sys.argv[0], *unknown]

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
