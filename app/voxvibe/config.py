"""Configuration management for VoxVibe using XDG Base Directory specification."""

import logging
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

logger = logging.getLogger(__name__)

# XDG Base Directory paths
XDG_CONFIG_HOME = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
XDG_DATA_HOME = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))

CONFIG_DIRS = [
    XDG_CONFIG_HOME / 'voxvibe',
]

CONFIG_FILENAME = 'config.toml'


@dataclass
class FasterWhisperConfig:
    """Configuration for faster-whisper backend."""
    model: str = "base"
    language: str = "en"
    device: Literal["auto", "cpu", "cuda"] = "auto"
    compute_type: Literal["auto", "int8", "int16", "float16", "float32"] = "auto"


@dataclass
class TranscriptionConfig:
    """Configuration for transcription backend and models."""
    backend: Literal["faster-whisper"] = "faster-whisper"
    faster_whisper: FasterWhisperConfig = field(default_factory=FasterWhisperConfig)


@dataclass
class AudioConfig:
    """Configuration for audio recording settings."""
    sample_rate: int = 16000
    channels: int = 1

@dataclass
class HotkeyConfig:
    """
    Configuration for hotkey management.
    
    Attributes:
        strategy (Literal["dbus", "qt", "auto"]): Preferred strategy for hotkey management.
    """
    strategy: Literal["dbus", "qt", "auto"] = "auto"


@dataclass
class UIConfig:
    """
    Configuration for user interface behavior.
    
    Attributes:
        startup_delay (float): The delay in seconds before initializing graphical components.
        show_notifications (bool): Whether to show notifications.
        minimize_to_tray (bool): Whether to minimize to tray.
    """
    startup_delay: float = 2.0
    show_notifications: bool = True
    minimize_to_tray: bool = True


@dataclass
class WindowManagerConfig:
    """
    Configuration for window management.
    
    Attributes:
        strategy (Literal["auto", "dbus", "xdotool"]): The preferred strategy for window management.
        paste_delay (float): The delay in seconds before pasting.
    """
    strategy: Literal["auto", "dbus", "xdotool"] = "auto"
    paste_delay: float = 0.1


@dataclass
class HistoryConfig:
    """
    Configuration for transcription history.
    
    Attributes:
        enabled (bool): Whether to store transcription history.
        max_entries (int): Maximum number of history entries to keep.
        storage_path (str): Path to the SQLite database file.
    """
    enabled: bool = True
    max_entries: int = 20
    storage_path: str = str(XDG_DATA_HOME / 'voxvibe' / 'history.db')


@dataclass
class LoggingConfig:
    """
    Configuration for logging.
    
    Attributes:
        level (str): The logging level.
        file (str): The path to the log file.
    """
    level: str = "INFO"
    file: str = str(XDG_DATA_HOME / 'voxvibe' / 'voxvibe.log')


@dataclass
class VoxVibeConfig:
    """
    Main configuration class for VoxVibe.
    
    Attributes:
        transcription (TranscriptionConfig): Configuration for transcription backend and models.
        audio (AudioConfig): Configuration for audio recording settings.
        hotkeys (HotkeyConfig): Configuration for hotkey management.
        ui (UIConfig): Configuration for user interface behavior.
        window_manager (WindowManagerConfig): Configuration for window management.
        history (HistoryConfig): Configuration for transcription history.
        logging (LoggingConfig): Configuration for logging.
    """
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    window_manager: WindowManagerConfig = field(default_factory=WindowManagerConfig)
    history: HistoryConfig = field(default_factory=HistoryConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


class ConfigurationError(Exception):
    """Raised when there's an error with configuration."""
    pass


def find_config_file() -> Optional[Path]:
    """Find the configuration file in XDG-compliant locations."""
    for config_dir in CONFIG_DIRS:
        config_file = config_dir / CONFIG_FILENAME
        if config_file.exists():
            logger.debug(f"Found configuration file: {config_file}")
            return config_file
    
    logger.debug("No configuration file found")
    return None


def load_config() -> VoxVibeConfig:
    """Load configuration from file or raise ConfigurationError if not found."""
    config_file = find_config_file()
    
    if config_file is None:
        raise ConfigurationError("No configuration file found")
    
    try:
        with open(config_file, 'rb') as f:
            config_data = tomllib.load(f)
        
        logger.info(f"Loaded configuration from {config_file}")
        return _parse_config(config_data)
    
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration from {config_file}: {e}")


def _parse_config(config_data: dict) -> VoxVibeConfig:
    """Parse configuration data into VoxVibeConfig object."""
    try:
        # Extract sections with defaults
        transcription_data = config_data.get('transcription', {})
        audio_data = config_data.get('audio', {})
        hotkeys_data = config_data.get('hotkeys', {})
        ui_data = config_data.get('ui', {})
        window_manager_data = config_data.get('window_manager', {})
        history_data = config_data.get('history', {})
        logging_data = config_data.get('logging', {})
        
        # Handle nested faster-whisper config with backward compatibility
        faster_whisper_data = transcription_data.pop('faster_whisper', {})
        
        # Handle backward compatibility: move old direct fields to faster_whisper section
        old_fields = ['model', 'language', 'device', 'compute_type']
        for field in old_fields:
            if field in transcription_data:
                faster_whisper_data[field] = transcription_data.pop(field)
        
        transcription_config = TranscriptionConfig(**transcription_data)
        transcription_config.faster_whisper = FasterWhisperConfig(**faster_whisper_data)
        
        # Create config objects
        return VoxVibeConfig(
            transcription=transcription_config,
            audio=AudioConfig(**audio_data),
            hotkeys=HotkeyConfig(**hotkeys_data),
            ui=UIConfig(**ui_data),
            window_manager=WindowManagerConfig(**window_manager_data),
            history=HistoryConfig(**history_data),
            logging=LoggingConfig(**logging_data),
        )
    
    except TypeError as e:
        raise ConfigurationError(f"Invalid configuration format: {e}")


def create_default_config() -> Path:
    """Create a default configuration file in user's config directory."""
    config_dir = XDG_CONFIG_HOME / 'voxvibe'
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = config_dir / CONFIG_FILENAME
    
    default_config = '''# VoxVibe Configuration File

[transcription]
# Options: "faster-whisper", default: "faster-whisper"
# backend = "faster-whisper"  

[transcription.faster_whisper]
# faster-whisper model options: tiny, tiny.en, base, base.en,
# small, small.en, distil-small.en, medium, medium.en, distil-medium.en,
# large-v1, large-v2, large-v3, large, distil-large-v2, distil-large-v3,
# large-v3-turbo, or turbo
# model = "base"            

# Language code or "auto" for auto-detection
# language = "en"

# Device options: "auto", "cpu", "cuda"
# device = "auto"

# Compute type options: "auto", "int8", "int16", "float16", "float32"
# compute_type = "auto"

[audio]

# Audio sample rate in Hz
sample_rate = 16000         

# Number of audio channels (1 = mono, 2 = stereo)
channels = 1                

[hotkeys]
# Options: "dbus", "qt", "auto"
# strategy = "auto"           

[ui]

# Seconds to wait before initializing graphical components
# startup_delay = 2.0         

# Other UI options
# show_notifications = true
# minimize_to_tray = true

[window_manager]
# Options: "auto", "dbus", "xdotool"
# strategy = "auto"
# Delay in seconds before pasting
# paste_delay = 0.1           

[history]
# Whether to store transcription history
# enabled = true              
# Maximum number of history entries to keep 
# max_entries = 20            
# SQLite database path (respects XDG_DATA_HOME)
# storage_path = "{XDG_DATA_HOME}/voxvibe/history.db"

[logging]
# Options: "DEBUG", "INFO", "WARNING", "ERROR"
# level = "INFO"
# Log file path (respects XDG_DATA_HOME)
# file = "{XDG_DATA_HOME}/voxvibe/voxvibe.log"
'''
    
    # Substitute XDG_DATA_HOME in the template
    default_config = default_config.format(XDG_DATA_HOME=XDG_DATA_HOME)
    
    with open(config_file, 'w') as f:
        f.write(default_config)
    
    logger.info(f"Created default configuration file: {config_file}")
    return config_file


def get_config() -> VoxVibeConfig:
    """Get configuration, creating default if none exists."""
    try:
        logger.info("Loading configuration")
        return load_config()
    except ConfigurationError:
        logger.warning("Failed to load configuration, creating default")
        create_default_config()
        return VoxVibeConfig()


# Global configuration instance (lazy-loaded)
_config_instance: Optional[VoxVibeConfig] = None


def config() -> VoxVibeConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = get_config()
    return _config_instance


def reload_config() -> VoxVibeConfig:
    """Reload configuration from file."""
    global _config_instance
    _config_instance = get_config()
    return _config_instance


def setup_logging(logging_config: Optional[LoggingConfig] = None) -> None:
    """Configure logging based on LoggingConfig settings."""
    if logging_config is None:
        logging_config = LoggingConfig()
    
    # Expand user path for log file
    log_file = Path(logging_config.file).expanduser()
    
    # Create log directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    import logging.handlers
    
    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - VoxVibe - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter(
        "%(asctime)s - VoxVibe - %(levelname)s - %(message)s"
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, logging_config.level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5  # 10MB files, keep 5 backups
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
    except Exception as e:
        logger.warning(f"Failed to setup file logging: {e}")
