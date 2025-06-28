from typing import TYPE_CHECKING

import numpy as np
import pytest

from voxvibe.config import TranscriptionConfig
from voxvibe.transcriber import Transcriber

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture
def mock_whisper_model(mocker: "MockerFixture"):
    """Mock WhisperModel to avoid loading actual models."""
    mock = mocker.patch('voxvibe.transcriber.WhisperModel')
    model_instance = mocker.MagicMock()
    mock.return_value = model_instance
    return model_instance


@pytest.fixture  
def transcriber(mock_whisper_model):
    """Create a Transcriber instance with mocked model."""
    return Transcriber()


def test_transcriber_init_default_config(mock_whisper_model):
    """Test transcriber initialization with default config."""
    transcriber = Transcriber()
    assert transcriber.config.backend == "faster-whisper"
    assert transcriber.config.model == "base"
    assert transcriber.config.language == "en"
    assert transcriber.config.device == "auto"
    assert transcriber.config.compute_type == "auto"


def test_transcriber_init_custom_config(mock_whisper_model):
    """Test transcriber initialization with custom config."""
    config = TranscriptionConfig(model="small", language="es", device="cpu")
    transcriber = Transcriber(config)
    assert transcriber.config.model == "small"
    assert transcriber.config.language == "es" 
    assert transcriber.config.device == "cpu"


def test_load_model_auto_device_cpu(mocker: "MockerFixture"):
    """Test model loading with auto device selection (defaults to CPU)."""
    mock_model = mocker.patch('voxvibe.transcriber.WhisperModel')
    mocker.patch('os.path.expanduser', return_value="/home/user/.cache/whisper")
    
    config = TranscriptionConfig(device="auto", compute_type="auto")
    Transcriber(config)
    
    mock_model.assert_called_once_with(
        "base",
        device="cpu",
        compute_type="int8",
        download_root="/home/user/.cache/whisper"
    )


def test_load_model_explicit_device(mocker: "MockerFixture"):
    """Test model loading with explicit device and compute type."""
    mock_model = mocker.patch('voxvibe.transcriber.WhisperModel')
    mocker.patch('os.path.expanduser', return_value="/home/user/.cache/whisper")
    
    config = TranscriptionConfig(device="cuda", compute_type="float16")
    Transcriber(config)
    
    mock_model.assert_called_once_with(
        "base",
        device="cuda", 
        compute_type="float16",
        download_root="/home/user/.cache/whisper"
    )


def test_transcribe_no_model(transcriber):
    """Test transcription when model is not loaded."""
    transcriber.model = None
    result = transcriber.transcribe(np.array([1.0, 2.0, 3.0]))
    assert result is None


def test_transcribe_no_audio_data(transcriber):
    """Test transcription with no audio data."""
    assert transcriber.transcribe(None) is None
    assert transcriber.transcribe(np.array([])) is None


def test_transcribe_audio_too_short(transcriber):
    """Test transcription with audio shorter than minimum length."""
    # Audio shorter than 0.1 seconds at 16kHz (1600 samples)
    short_audio = np.random.random(100).astype(np.float32)
    result = transcriber.transcribe(short_audio)
    assert result is None


def test_transcribe_audio_format_conversion(transcriber, mocker: "MockerFixture"):
    """Test that audio is converted to float32 format."""
    # Create int16 audio data
    audio_int16 = np.array([1000, 2000, 3000] * 1000, dtype=np.int16)
    
    # Mock successful transcription
    mock_segment = mocker.MagicMock()
    mock_segment.text = "Hello world"
    mock_info = mocker.MagicMock()
    mock_info.language = "en"
    mock_info.language_probability = 0.95
    
    transcriber.model.transcribe.return_value = ([mock_segment], mock_info)
    
    transcriber.transcribe(audio_int16)
    
    # Verify model was called with float32 data
    call_args = transcriber.model.transcribe.call_args[0]
    audio_passed = call_args[0]
    assert audio_passed.dtype == np.float32


def test_transcribe_audio_normalization(transcriber, mocker: "MockerFixture"):
    """Test that audio exceeding range [-1, 1] is normalized."""
    # Create audio with values > 1.0
    loud_audio = np.array([5.0, -3.0, 2.0] * 1000, dtype=np.float32)
    
    # Mock successful transcription  
    mock_segment = mocker.MagicMock()
    mock_segment.text = "Test"
    mock_info = mocker.MagicMock()
    mock_info.language = "en"
    mock_info.language_probability = 0.9
    
    transcriber.model.transcribe.return_value = ([mock_segment], mock_info)
    
    transcriber.transcribe(loud_audio)
    
    # Verify normalized audio was passed
    call_args = transcriber.model.transcribe.call_args[0]
    audio_passed = call_args[0]
    assert np.max(np.abs(audio_passed)) <= 1.0


def test_transcribe_language_handling(transcriber, mocker: "MockerFixture"):
    """Test language parameter handling."""
    audio = np.random.random(5000).astype(np.float32)
    
    mock_segment = mocker.MagicMock()
    mock_segment.text = "Test"
    mock_info = mocker.MagicMock()
    mock_info.language = "es"
    mock_info.language_probability = 0.9
    
    transcriber.model.transcribe.return_value = ([mock_segment], mock_info)
    
    # Test with explicit language
    transcriber.transcribe(audio, language="es")
    call_kwargs = transcriber.model.transcribe.call_args[1]
    assert call_kwargs['language'] == "es"
    
    # Test with auto language (should be None)
    transcriber.transcribe(audio, language="auto")
    call_kwargs = transcriber.model.transcribe.call_args[1]
    assert call_kwargs['language'] is None


def test_transcribe_successful(transcriber, mocker: "MockerFixture"):
    """Test successful transcription with multiple segments."""
    audio = np.random.random(5000).astype(np.float32)
    
    # Mock multiple segments
    segment1 = mocker.MagicMock()
    segment1.text = " Hello "
    segment2 = mocker.MagicMock()  
    segment2.text = " world! "
    
    mock_info = mocker.MagicMock()
    mock_info.language = "en"
    mock_info.language_probability = 0.95
    
    transcriber.model.transcribe.return_value = ([segment1, segment2], mock_info)
    
    result = transcriber.transcribe(audio)
    assert result == "Hello world!"


def test_transcribe_no_speech_detected(transcriber, mocker: "MockerFixture"):
    """Test transcription when no speech is detected."""
    audio = np.random.random(5000).astype(np.float32)
    
    mock_info = mocker.MagicMock()
    transcriber.model.transcribe.return_value = ([], mock_info)
    
    result = transcriber.transcribe(audio)
    assert result is None


def test_transcribe_empty_segments(transcriber, mocker: "MockerFixture"):
    """Test transcription with empty segment text."""
    audio = np.random.random(5000).astype(np.float32)
    
    mock_segment = mocker.MagicMock()
    mock_segment.text = "   "  # Only whitespace
    mock_info = mocker.MagicMock()
    
    transcriber.model.transcribe.return_value = ([mock_segment], mock_info)
    
    result = transcriber.transcribe(audio)
    assert result is None


def test_transcribe_exception_handling(transcriber):
    """Test that transcription exceptions are handled gracefully."""
    audio = np.random.random(5000).astype(np.float32)
    
    transcriber.model.transcribe.side_effect = Exception("Model error")
    
    result = transcriber.transcribe(audio)
    assert result is None


def test_get_available_models(transcriber):
    """Test getting list of available models."""
    models = transcriber.get_available_models()
    expected_models = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
    assert models == expected_models


def test_get_supported_languages(transcriber):
    """Test getting list of supported languages."""
    languages = transcriber.get_supported_languages()
    assert isinstance(languages, list)
    assert "en" in languages
    assert "es" in languages
    assert "fr" in languages
    assert len(languages) > 50  # Should have many languages


def test_load_model_exception(mocker: "MockerFixture"):
    """Test model loading exception handling."""
    mock_logger = mocker.patch('voxvibe.transcriber.logger')
    mock_model = mocker.patch('voxvibe.transcriber.WhisperModel')
    mock_model.side_effect = Exception("Model load failed")
    
    with pytest.raises(Exception):
        Transcriber()
    
    mock_logger.exception.assert_called_once()


def test_transcriber_config_defaults():
    """Test that TranscriptionConfig has expected defaults."""
    config = TranscriptionConfig()
    assert config.backend == "faster-whisper"
    assert config.model == "base"
    assert config.language == "en"
    assert config.device == "auto"
    assert config.compute_type == "auto"