#!/usr/bin/env python3
import logging
import signal
import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from .dbus_window_manager import DBusWindowManager
from .theme import apply_theme
from .ui import DictationApp


def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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


if __name__ == "__main__":
    main()
