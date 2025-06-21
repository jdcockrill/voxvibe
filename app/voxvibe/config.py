"""Configuration management for VoxVibe.

This module provides configuration management for VoxVibe settings,
including history retention and other user preferences.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class Config:
    """Manages VoxVibe configuration settings."""
    
    DEFAULT_CONFIG = {
        'history': {
            'enabled': True,
            'max_entries': 30,
            'retention_days': 30
        },
        'transcription': {
            'model_size': 'base',
            'language': 'en'
        }
    }
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config_path = self._get_config_path()
        self._config = self._load_config()
    
    def _get_config_path(self) -> Path:
        """Get the path to the configuration file."""
        # Create ~/.config/voxvibe/ directory if it doesn't exist
        config_dir = Path.home() / ".config" / "voxvibe"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged_config = self._merge_configs(self.DEFAULT_CONFIG, config)
                    logger.info(f"Loaded configuration from {self.config_path}")
                    return merged_config
            else:
                logger.info("No configuration file found, using defaults")
                self._save_config(self.DEFAULT_CONFIG)
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}, using defaults")
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user config with defaults."""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'history.max_entries')."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set a configuration value using dot notation and save to file."""
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save the updated configuration
        self._save_config(self._config)
    
    def get_history_enabled(self) -> bool:
        """Get whether history is enabled."""
        return self.get('history.enabled', True)
    
    def set_history_enabled(self, enabled: bool):
        """Set whether history is enabled."""
        self.set('history.enabled', enabled)
    
    def get_history_max_entries(self) -> int:
        """Get maximum number of history entries."""
        return self.get('history.max_entries', 30)
    
    def set_history_max_entries(self, max_entries: int):
        """Set maximum number of history entries."""
        if max_entries > 0:
            self.set('history.max_entries', max_entries)
    
    def get_history_retention_days(self) -> int:
        """Get history retention period in days."""
        return self.get('history.retention_days', 30)
    
    def set_history_retention_days(self, days: int):
        """Set history retention period in days."""
        if days > 0:
            self.set('history.retention_days', days)
    
    def get_transcription_model_size(self) -> str:
        """Get Whisper model size."""
        return self.get('transcription.model_size', 'base')
    
    def set_transcription_model_size(self, model_size: str):
        """Set Whisper model size."""
        self.set('transcription.model_size', model_size)
    
    def get_transcription_language(self) -> str:
        """Get transcription language."""
        return self.get('transcription.language', 'en')
    
    def set_transcription_language(self, language: str):
        """Set transcription language."""
        self.set('transcription.language', language)
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self._config = self.DEFAULT_CONFIG.copy()
        self._save_config(self._config)
        logger.info("Configuration reset to defaults")


# Global configuration instance
_config = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config