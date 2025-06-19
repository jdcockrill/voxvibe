#!/usr/bin/env python3
import signal
import sys
import logging

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
    apply_theme(app)
    
    window = DictationApp(window_manager)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
