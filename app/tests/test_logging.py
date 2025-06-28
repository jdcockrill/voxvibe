import logging
import logging.handlers
from pathlib import Path
from typing import TYPE_CHECKING

from voxvibe.config import LoggingConfig, setup_logging

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_setup_logging_default_config(mocker: "MockerFixture", tmp_path: Path):
    """Test setup_logging with default LoggingConfig."""
    # Mock expanduser to use tmp_path
    mock_expanduser = mocker.patch('pathlib.Path.expanduser')
    mock_expanduser.return_value = tmp_path / "voxvibe.log"
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    setup_logging()
    
    # Check that handlers were added
    assert len(root_logger.handlers) == 2  # console + file
    assert root_logger.level == logging.INFO
    
    # Check console handler
    console_handler = root_logger.handlers[0]
    assert isinstance(console_handler, logging.StreamHandler)
    assert "VoxVibe" in console_handler.formatter._fmt
    
    # Check file handler
    file_handler = root_logger.handlers[1]
    assert isinstance(file_handler, logging.handlers.RotatingFileHandler)
    assert file_handler.maxBytes == 10 * 1024 * 1024  # 10MB
    assert file_handler.backupCount == 5


def test_setup_logging_custom_config(tmp_path: Path):
    """Test setup_logging with custom LoggingConfig."""
    log_file = tmp_path / "custom.log"
    config = LoggingConfig(level="DEBUG", file=str(log_file))
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    setup_logging(config)
    
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 2


def test_setup_logging_creates_log_directory(tmp_path: Path):
    """Test that setup_logging creates log directory if it doesn't exist."""
    log_dir = tmp_path / "logs" / "subdir"
    log_file = log_dir / "voxvibe.log"
    config = LoggingConfig(file=str(log_file))
    
    # Ensure directory doesn't exist
    assert not log_dir.exists()
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    setup_logging(config)
    
    # Directory should be created
    assert log_dir.exists()
    assert log_dir.is_dir()


def test_setup_logging_path_expansion(mocker: "MockerFixture", tmp_path: Path):
    """Test that setup_logging expands user paths correctly."""
    # Mock expanduser to return our tmp_path
    mock_expanduser = mocker.patch('pathlib.Path.expanduser')
    expanded_path = tmp_path / "expanded" / "voxvibe.log"
    mock_expanduser.return_value = expanded_path
    
    config = LoggingConfig(file="~/logs/voxvibe.log")
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    setup_logging(config)
    
    # Check that expanduser was called
    mock_expanduser.assert_called_once()
    
    # Check that the expanded directory was created
    assert expanded_path.parent.exists()


def test_setup_logging_invalid_level():
    """Test setup_logging with invalid log level."""
    config = LoggingConfig(level="INVALID_LEVEL")
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    setup_logging(config)
    
    # Should fall back to INFO level
    assert root_logger.level == logging.INFO


def test_setup_logging_file_handler_exception(mocker: "MockerFixture", tmp_path: Path):
    """Test setup_logging when file handler creation fails."""
    mock_logger = mocker.patch('voxvibe.config.logger')
    
    # Mock RotatingFileHandler to raise exception
    mock_file_handler = mocker.patch('logging.handlers.RotatingFileHandler')
    mock_file_handler.side_effect = Exception("Permission denied")
    
    config = LoggingConfig(file=str(tmp_path / "test.log"))
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    setup_logging(config)
    
    # Should only have console handler
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0], logging.StreamHandler)
    
    # Should log warning about file handler failure
    mock_logger.warning.assert_called_once()


def test_setup_logging_clears_existing_handlers(mocker: "MockerFixture", tmp_path: Path):
    """Test that setup_logging clears existing handlers."""
    root_logger = logging.getLogger()
    
    # Add a dummy handler
    dummy_handler = logging.StreamHandler()
    root_logger.addHandler(dummy_handler)
    
    initial_handler_count = len(root_logger.handlers)
    assert initial_handler_count > 0
    
    # Mock expanduser to use tmp_path
    mock_expanduser = mocker.patch('pathlib.Path.expanduser')
    mock_expanduser.return_value = tmp_path / "voxvibe.log"
    
    setup_logging()
    
    # Should have exactly 2 handlers (console + file)
    assert len(root_logger.handlers) == 2
    # The dummy handler should be gone
    assert dummy_handler not in root_logger.handlers


def test_setup_logging_formatter_content():
    """Test that log formatters have expected content."""
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    setup_logging()
    
    console_handler = root_logger.handlers[0]
    file_handler = root_logger.handlers[1]
    
    # Check console formatter
    console_fmt = console_handler.formatter._fmt
    assert "%(asctime)s" in console_fmt
    assert "VoxVibe" in console_fmt
    assert "%(levelname)s" in console_fmt
    assert "%(message)s" in console_fmt
    
    # Check file formatter
    file_fmt = file_handler.formatter._fmt
    assert "%(asctime)s" in file_fmt
    assert "VoxVibe" in file_fmt
    assert "%(name)s" in file_fmt
    assert "%(levelname)s" in file_fmt
    assert "%(message)s" in file_fmt


def test_logging_config_defaults():
    """Test LoggingConfig default values."""
    config = LoggingConfig()
    assert config.level == "INFO"
    assert config.file == "~/.local/share/voxvibe/voxvibe.log"


def test_logging_config_custom_values():
    """Test LoggingConfig with custom values."""
    config = LoggingConfig(level="DEBUG", file="/tmp/custom.log")
    assert config.level == "DEBUG"
    assert config.file == "/tmp/custom.log"


def test_setup_logging_file_handler_configuration(mocker: "MockerFixture", tmp_path: Path):
    """Test that file handler is configured with correct parameters."""
    mock_file_handler_class = mocker.patch('logging.handlers.RotatingFileHandler')
    mock_file_handler = mocker.MagicMock()
    # Set the level attribute to a proper logging level
    mock_file_handler.level = logging.NOTSET
    mock_file_handler_class.return_value = mock_file_handler
    
    log_file = tmp_path / "test.log"
    config = LoggingConfig(file=str(log_file))
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    setup_logging(config)
    
    # Check that RotatingFileHandler was called with correct parameters
    mock_file_handler_class.assert_called_once_with(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    
    # Check that formatter was set
    mock_file_handler.setFormatter.assert_called_once()
    
    # Check that handler was added to root logger
    assert mock_file_handler in root_logger.handlers
