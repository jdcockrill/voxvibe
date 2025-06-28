import queue
import threading
from typing import TYPE_CHECKING

import numpy as np
import pytest

from voxvibe.audio_recorder import AudioRecorder
from voxvibe.config import AudioConfig

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture
def mock_sounddevice(mocker: "MockerFixture"):
    """Mock sounddevice module to avoid hardware dependencies."""
    return mocker.patch('voxvibe.audio_recorder.sd')


@pytest.fixture
def audio_recorder(mock_sounddevice):
    """Create AudioRecorder instance with mocked sounddevice."""
    return AudioRecorder()


def test_audio_recorder_init_default_config(mock_sounddevice):
    """Test AudioRecorder initialization with default config."""
    recorder = AudioRecorder()
    
    assert recorder.config.sample_rate == 16000
    assert recorder.config.channels == 1
    assert recorder.sample_rate == 16000
    assert recorder.channels == 1
    assert recorder.is_recording is False
    assert isinstance(recorder.audio_queue, queue.Queue)
    
    # Check sounddevice defaults are set
    mock_sounddevice.default.samplerate = 16000
    mock_sounddevice.default.channels = 1
    assert mock_sounddevice.default.dtype == np.float32


def test_audio_recorder_init_custom_config(mock_sounddevice):
    """Test AudioRecorder initialization with custom config."""
    config = AudioConfig(sample_rate=44100, channels=2)
    recorder = AudioRecorder(config)
    
    assert recorder.config.sample_rate == 44100
    assert recorder.config.channels == 2
    assert recorder.sample_rate == 44100
    assert recorder.channels == 2


def test_start_recording_when_not_recording(audio_recorder, mock_sounddevice):
    """Test starting recording when not already recording."""
    audio_recorder.start_recording()
    
    assert audio_recorder.is_recording is True
    assert isinstance(audio_recorder.recording_thread, threading.Thread)
    assert audio_recorder.recording_thread.is_alive()
    
    # Clean up
    audio_recorder.stop_recording()


def test_start_recording_when_already_recording(audio_recorder, mock_sounddevice):
    """Test starting recording when already recording (should be no-op)."""
    audio_recorder.is_recording = True
    original_thread = audio_recorder.recording_thread
    
    audio_recorder.start_recording()
    
    # Should not create new thread
    assert audio_recorder.recording_thread == original_thread


def test_stop_recording_when_not_recording(audio_recorder):
    """Test stopping recording when not recording."""
    result = audio_recorder.stop_recording()
    assert result is None


def test_stop_recording_with_no_audio_data(audio_recorder, mock_sounddevice):
    """Test stopping recording with no audio data in queue."""
    audio_recorder.start_recording()
    
    # Stop immediately without adding audio data
    result = audio_recorder.stop_recording()
    
    assert result is None
    assert audio_recorder.is_recording is False


def test_stop_recording_with_audio_data(audio_recorder, mock_sounddevice):
    """Test stopping recording with audio data in queue."""
    # Mock audio data
    audio_chunk1 = np.array([[0.1], [0.2], [0.3]], dtype=np.float32)
    audio_chunk2 = np.array([[0.4], [0.5], [0.6]], dtype=np.float32)
    
    audio_recorder.start_recording()
    
    # Add mock audio data to queue
    audio_recorder.audio_queue.put(audio_chunk1)
    audio_recorder.audio_queue.put(audio_chunk2)
    
    result = audio_recorder.stop_recording()
    
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert len(result) == 6  # 3 + 3 samples
    assert audio_recorder.is_recording is False


def test_stop_recording_stereo_to_mono_conversion(audio_recorder, mock_sounddevice):
    """Test stereo audio conversion to mono."""
    # Mock stereo audio data (2 channels)
    stereo_chunk = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
    
    audio_recorder.start_recording()
    audio_recorder.audio_queue.put(stereo_chunk)
    
    result = audio_recorder.stop_recording()
    
    assert result is not None
    assert result.ndim == 1  # Should be mono
    # Values should be averaged: (0.1+0.2)/2 = 0.15, (0.3+0.4)/2 = 0.35
    assert np.allclose(result, [0.15, 0.35])


def test_get_available_devices(audio_recorder, mock_sounddevice):
    """Test getting available input devices."""
    # Mock device data
    mock_devices = [
        {"name": "Microphone 1", "max_input_channels": 1, "max_output_channels": 0, "default_samplerate": 44100},
        {"name": "Microphone 2", "max_input_channels": 2, "max_output_channels": 0, "default_samplerate": 48000},
        {"name": "Speaker", "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 44100},
    ]
    mock_sounddevice.query_devices.return_value = mock_devices
    
    devices = audio_recorder.get_available_devices()
    
    assert len(devices) == 2  # Only input devices
    assert devices[0]["id"] == 0
    assert devices[0]["name"] == "Microphone 1"
    assert devices[0]["channels"] == 1
    assert devices[0]["sample_rate"] == 44100
    
    assert devices[1]["id"] == 1
    assert devices[1]["name"] == "Microphone 2"
    assert devices[1]["channels"] == 2
    assert devices[1]["sample_rate"] == 48000


def test_get_available_devices_no_input_devices(audio_recorder, mock_sounddevice):
    """Test getting available devices when no input devices exist."""
    mock_devices = [
        {"name": "Speaker", "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 44100},
    ]
    mock_sounddevice.query_devices.return_value = mock_devices
    
    devices = audio_recorder.get_available_devices()
    assert len(devices) == 0


def test_set_device_success(audio_recorder, mock_sounddevice):
    """Test setting audio device successfully."""
    # Mock the device property as a list-like object
    mock_sounddevice.default.device = [None, None]
    
    result = audio_recorder.set_device(1)
    
    assert result is True
    assert mock_sounddevice.default.device[0] == 1


def test_set_device_failure(audio_recorder, mock_sounddevice, mocker: "MockerFixture"):
    """Test setting audio device with exception."""
    mock_logger = mocker.patch('voxvibe.audio_recorder.logger')
    
    # Mock device setting to raise exception
    def mock_device_setter(value):
        raise Exception("Device not found")
    
    # Mock the device property setter
    type(mock_sounddevice.default).device = mocker.PropertyMock(side_effect=mock_device_setter)
    
    result = audio_recorder.set_device(999)
    
    assert result is False
    mock_logger.exception.assert_called_once()

def test_recording_thread_exception_handling(audio_recorder, mock_sounddevice, mocker: "MockerFixture"):
    """Test that recording thread exceptions are handled gracefully."""
    mock_logger = mocker.patch('voxvibe.audio_recorder.logger')
    
    # Mock InputStream to raise exception
    mock_sounddevice.InputStream.side_effect = Exception("Audio system error")
    
    audio_recorder.start_recording()
    
    # Wait a bit for thread to process
    if audio_recorder.recording_thread:
        audio_recorder.recording_thread.join(timeout=1.0)
    
    # Should not crash, exception should be logged
    mock_logger.exception.assert_called_once()


def test_audio_config_defaults():
    """Test AudioConfig default values."""
    config = AudioConfig()
    assert config.sample_rate == 16000
    assert config.channels == 1


def test_audio_config_custom_values():
    """Test AudioConfig with custom values."""
    config = AudioConfig(sample_rate=44100, channels=2)
    assert config.sample_rate == 44100
    assert config.channels == 2


def test_concurrent_start_stop_recording(audio_recorder, mock_sounddevice):
    """Test concurrent start/stop operations."""
    # Start recording
    audio_recorder.start_recording()
    assert audio_recorder.is_recording is True
    
    # Stop recording
    audio_recorder.stop_recording()
    assert audio_recorder.is_recording is False
    
    # Start again
    audio_recorder.start_recording()
    assert audio_recorder.is_recording is True
    
    # Clean up
    audio_recorder.stop_recording()


def test_queue_empty_exception_handling(audio_recorder, mock_sounddevice, mocker: "MockerFixture"):
    """Test handling of queue.Empty exception during stop_recording."""
    # Mock queue to raise Empty exception
    mock_queue = mocker.patch.object(audio_recorder, 'audio_queue')
    mock_queue.empty.return_value = False
    mock_queue.get_nowait.side_effect = queue.Empty()
    
    audio_recorder.start_recording()
    result = audio_recorder.stop_recording()
    
    # Should handle exception gracefully
    assert result is None