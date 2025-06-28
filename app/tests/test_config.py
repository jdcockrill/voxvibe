import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from voxvibe.config import (
    CONFIG_FILENAME,
    AudioConfig,
    ConfigurationError,
    HotkeyConfig,
    LoggingConfig,
    TranscriptionConfig,
    UIConfig,
    VoxVibeConfig,
    WindowManagerConfig,
    _parse_config,
    config,
    create_default_config,
    find_config_file,
    get_config,
    load_config,
    reload_config,
)

if TYPE_CHECKING:
    from pytest_mock import MagicMock, MockerFixture


@pytest.fixture
def mock_xdg_config_home(mocker: "MockerFixture") -> "MagicMock":
    """Fixture to mock XDG_CONFIG_HOME and related paths."""
    mock_path = mocker.MagicMock(spec=Path)
    mocker.patch("voxvibe.config.XDG_CONFIG_HOME", mock_path)
    return mock_path


def test_find_config_file_found(mocker: "MockerFixture", mock_xdg_config_home: "MagicMock") -> None:
    """Test that find_config_file returns the correct path when a config file exists."""
    config_dir = mock_xdg_config_home / "voxvibe"
    config_file = config_dir / CONFIG_FILENAME

    mocker.patch("voxvibe.config.CONFIG_DIRS", [config_dir])
    mocker.patch.object(config_file, "exists", return_value=True)

    assert find_config_file() == config_file


def test_find_config_file_not_found(mocker: "MockerFixture", mock_xdg_config_home: "MagicMock") -> None:
    """Test that find_config_file returns None when no config file exists."""
    config_dir = mock_xdg_config_home / "voxvibe"
    config_file = config_dir / CONFIG_FILENAME

    mocker.patch("voxvibe.config.CONFIG_DIRS", [config_dir])
    mocker.patch.object(config_file, "exists", return_value=False)

    assert find_config_file() is None


def test_load_config_uses_defaults(mocker: "MockerFixture") -> None:
    """Test that load_config raises error when no config file is found."""
    mocker.patch("voxvibe.config.find_config_file", return_value=None)
    
    with pytest.raises(ConfigurationError, match="No configuration file found"):
        load_config()


def test_load_config_from_file(mocker: "MockerFixture") -> None:
    """Test that load_config correctly loads and parses a TOML config file."""
    mock_config_content: bytes = b"""
[transcription]
model = "small"

[ui]
startup_delay = 3.0
"""
    mock_path: Path = Path("/fake/config.toml")
    mocker.patch("voxvibe.config.find_config_file", return_value=mock_path)
    mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))

    config: VoxVibeConfig = load_config()

    assert config.transcription.model == "small"
    assert config.transcription.backend == "faster-whisper"  # Default
    assert config.ui.startup_delay == 3.0
    assert config.hotkeys == HotkeyConfig()  # Default


def test_load_config_invalid_format(mocker: "MockerFixture") -> None:
    """Test that load_config raises ConfigurationError for a malformed config file."""
    mock_config_content: bytes = b"this is not toml"
    mock_path: Path = Path("/fake/config.toml")
    mocker.patch("voxvibe.config.find_config_file", return_value=mock_path)
    mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))

    with pytest.raises(ConfigurationError):
        load_config()


def test_create_default_config_matches_dataclasses(tmp_path: Path, mocker: "MockerFixture") -> None:
    """Verify that the default config file content matches the dataclass defaults."""
    # Mock XDG_CONFIG_HOME to use the temporary directory
    mocker.patch("voxvibe.config.XDG_CONFIG_HOME", tmp_path)

    # Create the default config file
    config_file_path: Path = create_default_config()

    # Read the generated config file
    with open(config_file_path, "rb") as f:
        generated_config_data = tomllib.load(f)

    # Get the default config from the dataclasses
    default_config: VoxVibeConfig = VoxVibeConfig()

    # Compare the generated config with the dataclass defaults
    assert generated_config_data["transcription"]["backend"] == default_config.transcription.backend
    assert generated_config_data["transcription"]["model"] == default_config.transcription.model
    assert generated_config_data["hotkeys"]["strategy"] == default_config.hotkeys.strategy
    assert generated_config_data["ui"]["startup_delay"] == default_config.ui.startup_delay
    assert generated_config_data["ui"]["show_notifications"] == default_config.ui.show_notifications
    assert generated_config_data["ui"]["minimize_to_tray"] == default_config.ui.minimize_to_tray
    assert generated_config_data["window_manager"]["strategy"] == default_config.window_manager.strategy
    assert generated_config_data["window_manager"]["paste_delay"] == default_config.window_manager.paste_delay
    assert generated_config_data["logging"]["level"] == default_config.logging.level
    assert generated_config_data["logging"]["file"] == default_config.logging.file


def test_full_config_loading(mocker: "MockerFixture") -> None:
    """Test loading a complete config file with all sections and values defined."""
    config_content = b"""
# VoxVibe Configuration File
# This file follows the XDG Base Directory specification

[transcription]
backend = "faster-whisper"
model = "large-v3"

[hotkeys]
strategy = "dbus"

[ui]
startup_delay = 1.0
show_notifications = false
minimize_to_tray = false

[window_manager]
strategy = "xdotool"
paste_delay = 0.5

[logging]
level = "DEBUG"
file = "/tmp/voxvibe.log"
"""
    mocker.patch("voxvibe.config.find_config_file", return_value=Path("/fake/path.toml"))
    mocker.patch("builtins.open", mocker.mock_open(read_data=config_content))

    config = load_config()

    assert config.transcription == TranscriptionConfig(backend="faster-whisper", model="large-v3")
    assert config.hotkeys == HotkeyConfig(strategy="dbus")
    assert config.ui == UIConfig(startup_delay=1.0, show_notifications=False, minimize_to_tray=False)
    assert config.window_manager == WindowManagerConfig(strategy="xdotool", paste_delay=0.5)
    assert config.logging == LoggingConfig(level="DEBUG", file="/tmp/voxvibe.log")


def test_partial_config_loading(mocker: "MockerFixture") -> None:
    """Test that missing sections in the config file are filled with default values."""
    config_content = b"""
[transcription]
model = "small"

[ui]
show_notifications = false
"""
    mocker.patch("voxvibe.config.find_config_file", return_value=Path("/fake/path.toml"))
    mocker.patch("builtins.open", mocker.mock_open(read_data=config_content))

    config = load_config()

    # Check specified values
    assert config.transcription.model == "small"
    assert config.ui.show_notifications is False

    # Check that other values are default
    assert config.transcription.backend == TranscriptionConfig().backend
    assert config.hotkeys == HotkeyConfig()
    assert config.ui.startup_delay == UIConfig().startup_delay
    assert config.window_manager == WindowManagerConfig()
    assert config.logging == LoggingConfig()


def test_empty_config_file(mocker: "MockerFixture") -> None:
    """Test that an empty config file results in all default values."""
    mocker.patch("voxvibe.config.find_config_file", return_value=Path("/fake/path.toml"))
    mocker.patch("builtins.open", mocker.mock_open(read_data=b""))

    config = load_config()
    assert config == VoxVibeConfig()


def test_config_with_extra_values(mocker: "MockerFixture") -> None:
    """Test that extra values in the config file are ignored."""
    config_content = b"""
[transcription]
model = "base"
extra_key = "should be ignored"
"""
    mocker.patch("voxvibe.config.find_config_file", return_value=Path("/fake/path.toml"))
    mocker.patch("builtins.open", mocker.mock_open(read_data=config_content))

    with pytest.raises(ConfigurationError):
        load_config()


def test_audio_config_defaults() -> None:
    """Test AudioConfig default values."""
    config = AudioConfig()
    assert config.sample_rate == 16000
    assert config.channels == 1


def test_audio_config_custom_values() -> None:
    """Test AudioConfig with custom values."""
    config = AudioConfig(sample_rate=44100, channels=2)
    assert config.sample_rate == 44100
    assert config.channels == 2


def test_config_with_audio_section(mocker: "MockerFixture") -> None:
    """Test loading config with audio section."""
    config_content = b"""
[audio]
sample_rate = 44100
channels = 2

[transcription]
model = "small"
"""
    mocker.patch("voxvibe.config.find_config_file", return_value=Path("/fake/path.toml"))
    mocker.patch("builtins.open", mocker.mock_open(read_data=config_content))

    config = load_config()
    assert config.audio.sample_rate == 44100
    assert config.audio.channels == 2
    assert config.transcription.model == "small"


def test_get_config_success(mocker: "MockerFixture") -> None:
    """Test get_config when config loading succeeds."""
    mock_load_config = mocker.patch("voxvibe.config.load_config")
    mock_config = VoxVibeConfig()
    mock_load_config.return_value = mock_config
    
    result = get_config()
    assert result == mock_config
    mock_load_config.assert_called_once()


def test_get_config_failure_creates_default(mocker: "MockerFixture") -> None:
    """Test get_config creates default config when loading fails."""
    mock_load_config = mocker.patch("voxvibe.config.load_config")
    mock_load_config.side_effect = ConfigurationError("Config not found")
    
    mock_create_default = mocker.patch("voxvibe.config.create_default_config")
    mock_logger = mocker.patch("voxvibe.config.logger")
    
    result = get_config()
    
    # Should return default config
    assert result == VoxVibeConfig()
    mock_create_default.assert_called_once()
    mock_logger.warning.assert_called_once()


def test_config_global_instance(mocker: "MockerFixture") -> None:
    """Test global config instance caching."""
    mock_get_config = mocker.patch("voxvibe.config.get_config")
    mock_config = VoxVibeConfig()
    mock_get_config.return_value = mock_config
    
    # Reset global instance
    import voxvibe.config
    voxvibe.config._config_instance = None
    
    # First call should load config
    result1 = config()
    assert result1 == mock_config
    mock_get_config.assert_called_once()
    
    # Second call should use cached instance
    result2 = config()
    assert result2 == mock_config
    # get_config should still only be called once
    mock_get_config.assert_called_once()


def test_reload_config(mocker: "MockerFixture") -> None:
    """Test config reloading."""
    mock_get_config = mocker.patch("voxvibe.config.get_config")
    mock_config = VoxVibeConfig()
    mock_get_config.return_value = mock_config
    
    result = reload_config()
    assert result == mock_config
    mock_get_config.assert_called_once()


def test_parse_config_with_invalid_dataclass_field() -> None:
    """Test _parse_config with invalid field in dataclass."""
    config_data = {
        "transcription": {
            "model": "base",
            "invalid_field": "value"
        }
    }
    
    with pytest.raises(ConfigurationError):
        _parse_config(config_data)


def test_load_config_no_file_found(mocker: "MockerFixture") -> None:
    """Test load_config raises error when no config file is found."""
    mocker.patch("voxvibe.config.find_config_file", return_value=None)
    
    with pytest.raises(ConfigurationError, match="No configuration file found"):
        load_config()


def test_load_config_file_read_error(mocker: "MockerFixture") -> None:
    """Test load_config handles file read errors."""
    mock_path = Path("/fake/config.toml")
    mocker.patch("voxvibe.config.find_config_file", return_value=mock_path)
    mocker.patch("builtins.open", side_effect=IOError("Permission denied"))
    
    with pytest.raises(ConfigurationError, match="Failed to load configuration"):
        load_config()
