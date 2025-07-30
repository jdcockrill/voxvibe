#!/usr/bin/env python3
import argparse
import logging
import sys
import time

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from .config import ConfigurationError, config, create_default_config, setup_logging
from .signal_wakeup_handler import SignalWakeupHandler
from .single_instance import SingleInstance, SingleInstanceError

# Basic logging setup for startup (will be reconfigured later)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - VoxVibe - %(levelname)s - %(message)s")


def wait_for_system_tray(max_wait_seconds=30, check_interval=1):
    """Wait for system tray to become available with retry logic
    
    Args:
        max_wait_seconds: Maximum time to wait in seconds (default: 30)
        check_interval: Time between checks in seconds (default: 1)
        
    Returns:
        bool: True if system tray becomes available, False if timeout
    """
    logging.info(f"Waiting for system tray availability (max {max_wait_seconds}s)...")
    
    for attempt in range(max_wait_seconds):
        if QSystemTrayIcon.isSystemTrayAvailable():
            logging.info(f"System tray available after {attempt + 1} seconds")
            return True
        
        if attempt < max_wait_seconds - 1:  # Don't sleep on the last attempt
            time.sleep(check_interval)
    
    logging.error(f"System tray not available after {max_wait_seconds} seconds")
    return False


def main():
    """Run VoxVibe as a background service with system tray"""
    from .service import VoxVibeService

    parser = argparse.ArgumentParser(description="VoxVibe - Voice transcription service")
    parser.add_argument("--reset", action="store_true", help="Clear any stale single-instance lock and exit")
    parser.add_argument("--create-config", action="store_true", help="Create a default configuration file and exit")
    args = parser.parse_args()

    try:
        with SingleInstance("voxvibe_service_instance", reset=args.reset):
            if args.reset:
                logging.info("Service single-instance lock reset successfully.")
                return 0
            
            if args.create_config:
                config_path = create_default_config()
                logging.info(f"Created default configuration file at: {config_path}")
                return 0

            app = QApplication(sys.argv)
            # Initialize wakeup handler to bridge system signals into Qt loop
            _signal_wakeup = SignalWakeupHandler(app)

            app.setQuitOnLastWindowClosed(False)  # Don't quit when windows are closed
            app.setApplicationName("VoxVibe Service")

            # Check if system tray is available with retry logic
            if not wait_for_system_tray():
                logging.error("System tray is not available after waiting")
                return 1

            # Load configuration with proper error handling
            try:
                app_config = config()
            except ConfigurationError as e:
                logging.error(f"Configuration error: {e}")
                logging.error("To create a default configuration file, run: voxvibe --create-config")
                return 1
            
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
