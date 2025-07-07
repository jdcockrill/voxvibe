"""Main window manager class that orchestrates different strategies."""

import logging
from typing import List, Optional

from ..config import WindowManagerConfig
from ..models import WindowInfo
from .base import WindowManagerStrategy
from .dbus_strategy import DBusWindowManagerStrategy

logger = logging.getLogger(__name__)


class WindowManager:
    """Window manager that tries different strategies in preference order."""

    def __init__(self, config: Optional[WindowManagerConfig] = None, strategies: Optional[List[WindowManagerStrategy]] = None):
        """Initialize window manager with configuration and optional custom strategies.

        Args:
            config: WindowManagerConfig object with strategy preferences
            strategies: List of strategies to try in order. If None, uses config or default strategies.
        """
        self.config = config or WindowManagerConfig()
        
        if strategies is None:
            strategies = self._create_strategies_from_config()

        self._strategies = strategies
        self._active_strategy: Optional[WindowManagerStrategy] = None
        self._initialize_strategy()

    def _create_strategies_from_config(self) -> List[WindowManagerStrategy]:
        """Create strategy list based on configuration."""
        # Only use DBus strategy now
        return [DBusWindowManagerStrategy()]

    def _initialize_strategy(self) -> None:
        """Find and initialize the first available strategy."""
        for strategy in self._strategies:
            logger.debug(f"Checking availability of strategy: {strategy.get_strategy_name()}")
            try:
                if strategy.is_available():
                    self._active_strategy = strategy
                    logger.info(f"Using window manager strategy: {strategy.get_strategy_name()}")
                    return
            except Exception as e:
                logger.warning(f"Strategy {strategy.get_strategy_name()} failed availability check: {e}")
                continue

        logger.error("No window manager strategies are available")
        self._active_strategy = None

    def is_available(self) -> bool:
        """Check if any window manager strategy is available."""
        return self._active_strategy is not None

    def store_current_window(self) -> None:
        """Store information about the currently focused window."""
        if not self._active_strategy:
            logger.error("No active window manager strategy")
            return

        try:
            self._active_strategy.store_current_window()
        except Exception as e:
            logger.exception(f"Failed to store current window: {e}")
            # Try to fall back to next available strategy
            self._try_fallback_strategy()
            if self._active_strategy:
                try:
                    self._active_strategy.store_current_window()
                except Exception as fallback_error:
                    logger.exception(f"Fallback strategy also failed: {fallback_error}")

    def focus_and_paste(self, text: str) -> bool:
        """Focus the previously stored window and paste text into it.

        Args:
            text: The text to paste

        Returns:
            True if successful, False otherwise
        """
        if not self._active_strategy:
            logger.error("No active window manager strategy")
            return False

        try:
            return self._active_strategy.focus_and_paste(text)
        except Exception as e:
            logger.exception(f"Failed to focus and paste: {e}")
            # Try to fall back to next available strategy
            self._try_fallback_strategy()
            if self._active_strategy:
                try:
                    return self._active_strategy.focus_and_paste(text)
                except Exception as fallback_error:
                    logger.exception(f"Fallback strategy also failed: {fallback_error}")
            return False

    def _try_fallback_strategy(self) -> None:
        """Try to find an alternative strategy if the current one fails."""
        if not self._active_strategy:
            return

        current_strategy = self._active_strategy
        logger.warning(f"Strategy {current_strategy.get_strategy_name()} failed, trying fallback")

        # Find the next available strategy after the current one
        current_index = self._strategies.index(current_strategy)
        for strategy in self._strategies[current_index + 1 :]:
            try:
                if strategy.is_available():
                    self._active_strategy = strategy
                    logger.info(f"Switched to fallback strategy: {strategy.get_strategy_name()}")
                    return
            except Exception as e:
                logger.warning(f"Fallback strategy {strategy.get_strategy_name()} failed check: {e}")
                continue

        # No fallback found
        self._active_strategy = None
        logger.error("No fallback window manager strategies available")

    def get_active_strategy_name(self) -> str:
        """Get the name of the currently active strategy."""
        if self._active_strategy:
            return self._active_strategy.get_strategy_name()
        return "None"

    def get_available_strategies(self) -> List[str]:
        """Get list of all available strategy names."""
        available = []
        for strategy in self._strategies:
            try:
                if strategy.is_available():
                    available.append(strategy.get_strategy_name())
            except Exception:
                continue
        return available

    def get_stored_window_info(self) -> Optional[WindowInfo]:
        """Get stored window information from the active strategy.
        
        Returns:
            WindowInfo TypedDict containing window information if available, None otherwise
        """
        if not self._active_strategy:
            logger.warning("No active window manager strategy")
            return None
        
        return self._active_strategy.get_stored_window_info()

    def get_diagnostics(self) -> dict:
        """Get comprehensive diagnostics for all strategies."""
        diagnostics = {
            "active_strategy": self.get_active_strategy_name(),
            "available_strategies": self.get_available_strategies(),
            "all_strategies": {},
        }

        for strategy in self._strategies:
            try:
                strategy_name = strategy.get_strategy_name()
                diagnostics["all_strategies"][strategy_name] = strategy.get_diagnostics()
            except Exception as e:
                strategy_name = strategy.__class__.__name__
                diagnostics["all_strategies"][strategy_name] = {"error": str(e), "available": False}

        return diagnostics
