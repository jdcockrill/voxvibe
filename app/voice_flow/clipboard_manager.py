import pyperclip
from typing import Optional


class ClipboardManager:
        
    def set_text(self, text: str) -> bool:
        """
        Set text to clipboard.
        
        Args:
            text: Text to copy to clipboard
            
        Returns:
            True if successful, False otherwise
        """
        if not text:
            return False
        
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            print(f"pyperclip failed: {e}")
            return False
    
    def get_text(self) -> Optional[str]:
        """
        Get text from clipboard.
        
        Returns:
            Clipboard text or None if failed
        """
        try:
            return pyperclip.paste()
        except Exception as e:
            print(f"pyperclip paste failed: {e}")
            return None

    def clear(self) -> bool:
        """
        Clear the clipboard.
        
        Returns:
            True if successful, False otherwise
        """
        return self.set_text("")
