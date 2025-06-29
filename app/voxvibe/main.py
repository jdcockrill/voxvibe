#!/usr/bin/env python3
import argparse
import logging
import sys

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from .config import config, setup_logging
from .signal_wakeup_handler import SignalWakeupHandler
from .single_instance import SingleInstance, SingleInstanceError

# Basic logging setup for startup (will be reconfigured later)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - VoxVibe - %(levelname)s - %(message)s")


def main():
    """Run VoxVibe as a background service with system tray"""
    from .service import VoxVibeService

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--reset", action="store_true", help="Clear any stale single-instance lock and exit")
    args = parser.parse_args()

    try:
        with SingleInstance("voxvibe_service_instance", reset=args.reset):
            if args.reset:
                logging.info("Service single-instance lock reset successfully.")
                return 0

            app = QApplication(sys.argv)
            # Initialize wakeup handler to bridge system signals into Qt loop
            _signal_wakeup = SignalWakeupHandler(app)

            app.setQuitOnLastWindowClosed(False)  # Don't quit when windows are closed
            app.setApplicationName("VoxVibe Service")

            # Check if system tray is available
            if not QSystemTrayIcon.isSystemTrayAvailable():
                logging.error("System tray is not available on this system")
                return 1

            # Load configuration
            app_config = config()
            
            # Setup logging based on configuration
            setup_logging(app_config.logging)
            
            service = VoxVibeService(app, app_config)
            if not service.start():
                logging.error("Failed to start VoxVibe service")
                return 1

            logging.info("VoxVibe service started successfully")
            return app.exec()

    except SingleInstanceError as e:
        logging.error(e)
        return 1


if __name__ == "__main__":
    main()
