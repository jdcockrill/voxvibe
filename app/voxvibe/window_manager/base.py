"""Base interface for window manager strategies."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class WindowManagerStrategy(ABC):
    """Abstract base class for window manager implementations."""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this strategy is available on the current system."""
        pass
    
    @abstractmethod
    def store_current_window(self) -> None:
        """Store information about the currently focused window."""
        pass
    
    @abstractmethod
    def focus_and_paste(self, text: str) -> bool:
        """Focus the previously stored window and paste text into it.
        
        Args:
            text: The text to paste
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get a human-readable name for this strategy."""
        pass
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about this strategy.
        
        Returns:
            Dictionary with diagnostic information
        """
        return {
            'strategy': self.get_strategy_name(),
            'available': self.is_available()
        }