"""Xdotool-based window manager strategy."""

import logging
import os
import subprocess
import time
from typing import Any, Dict, Optional

import pyperclip

from .base import WindowManagerStrategy

logger = logging.getLogger(__name__)


class XdotoolWindowManagerStrategy(WindowManagerStrategy):
    """Window manager strategy using xdotool."""

    def __init__(self):
        self._stored_window_info: Optional[Dict[str, Any]] = None

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH."""
        try:
            subprocess.run(["which", command], capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def is_available(self) -> bool:
        """Check if this strategy is available on the current system."""

        # Check if xdotool is available
        if not self._command_exists("xdotool"):
            return False

        # Test basic xdotool functionality
        try:
            result = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, timeout=5)
            return result.returncode == 0 and int(result.stdout.strip()) > 0
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            return False

    def store_current_window(self) -> None:
        """Store information about the currently focused window."""
        try:
            # Get focused window ID
            result = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                raise RuntimeError(f"Failed to get active window: {result.stderr}")

            window_id = result.stdout.strip()
            if not window_id:
                raise RuntimeError("No active window ID returned")

            # Get window class
            class_result = subprocess.run(
                ["xdotool", "getwindowclassname", window_id], capture_output=True, text=True, timeout=5
            )
            window_class = class_result.stdout.strip() if class_result.returncode == 0 else ""

            # Get window title
            title_result = subprocess.run(
                ["xdotool", "getwindowname", window_id], capture_output=True, text=True, timeout=5
            )
            window_title = title_result.stdout.strip() if title_result.returncode == 0 else ""

            self._stored_window_info = {
                "id": window_id,
                "class": window_class,
                "title": window_title,
                "method": "xdotool",
            }

            logger.debug(f"Stored window: {window_title} (ID: {window_id}, Class: {window_class})")

        except subprocess.TimeoutExpired:
            raise RuntimeError("Xdotool command timed out")
        except FileNotFoundError:
            raise RuntimeError("Xdotool command not found")
        except Exception as e:
            raise RuntimeError(f"Failed to store current window: {e}")

    def focus_and_paste(self, text: str) -> bool:
        """Focus the previously stored window and paste text into it.

        Args:
            text: The text to paste

        Returns:
            True if successful, False otherwise
        """
        if not self._stored_window_info:
            logger.warning("No stored window information")
            return False

        window_id = self._stored_window_info.get("id")
        if not window_id:
            logger.warning("No valid window ID in stored information")
            return False

        try:
            # Focus the window
            focus_result = subprocess.run(["xdotool", "windowactivate", window_id], capture_output=True, timeout=5)
            if focus_result.returncode != 0:
                logger.warning(f"Failed to focus window {window_id}: {focus_result.stderr}")
                return False

            # Small delay to ensure window is focused
            time.sleep(0.1)

            # Paste text using clipboard + Ctrl+V
            success = self._paste_via_clipboard(text, window_id)

            if success:
                logger.debug(f"Successfully pasted text to window {window_id}")
            else:
                logger.warning(f"Failed to paste text to window {window_id}")

            return success

        except subprocess.TimeoutExpired:
            logger.error("Xdotool focus command timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to focus and paste: {e}")
            return False

    def _paste_via_clipboard(self, text: str, window_id: str) -> bool:
        """Paste text by copying to clipboard and simulating Ctrl+V."""
        try:
            # Copy text to clipboard
            pyperclip.copy(text)

            # Small delay to ensure clipboard is updated
            time.sleep(0.05)

            # Simulate Ctrl+v
            result = subprocess.run(
                ["xdotool", "key", "--clearmodifiers", "--window", window_id, "ctrl+v"], capture_output=True, timeout=5
            )
            return result.returncode == 0

        except Exception as e:
            logger.error(f"Clipboard paste failed: {e}")
            return False

    def get_strategy_name(self) -> str:
        """Get a human-readable name for this strategy."""
        return "Xdotool (X11)"

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about this strategy."""
        base_diagnostics = super().get_diagnostics()

        # Add xdotool-specific diagnostics
        xdotool_diagnostics = {
            "xdotool_available": self._command_exists("xdotool"),
            "stored_window": self._stored_window_info,
            "x11_display": os.environ.get("DISPLAY", "Not set"),
            "wayland_display": os.environ.get("WAYLAND_DISPLAY", "Not set"),
        }

        base_diagnostics.update(xdotool_diagnostics)
        return base_diagnostics
