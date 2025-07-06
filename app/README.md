# VoxVibe Python Application

The VoxVibe Python application is a sophisticated voice dictation service that runs as a background daemon, providing seamless speech-to-text functionality with system-level integration. Built on PyQt6, it features a modular architecture with pluggable strategies for different desktop environments and hotkey management approaches.

## Architecture Overview

VoxVibe follows a service-oriented architecture with multiple components working together:

```
┌─────────────────────────────────────────────────────────────────┐
│                        VoxVibe Service                          │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │  State Manager  │  │  System Tray     │  │ Single Instance │ │
│  │  (FSM)          │  │  Integration     │  │ Manager         │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Audio Recorder  │  │   Transcriber    │  │ Window Manager  │ │
│  │ (sounddevice)   │  │ (faster-whisper) │  │  (Strategies)   │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │               Hotkey Manager (Strategies)                   │ │
│  │  ┌───────────────────┐    ┌─────────────────────────────┐   │ │
│  │  │ Qt Hotkey (Alpha) │    │   DBus Hotkey (Preferred)   │   │ │
│  │  │   (pynput)        │    │  (GNOME Extension)          │   │ │
│  │  └───────────────────┘    └─────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                                          │
         ▼                                          ▼
┌─────────────────┐                        ┌─────────────────┐
│ Audio Hardware  │                        │ GNOME Extension │
│   (Microphone)  │                        │  (Window Mgmt)  │
└─────────────────┘                        └─────────────────┘
```

## Core Components

### Service Architecture (`service.py`)

**VoxVibeService** - Central orchestrator that coordinates all subsystems:
- **Lifecycle Management**: Initializes and manages all components
- **Event-Driven**: Qt6 signal-slot architecture for component communication
- **Background Service**: Runs as persistent daemon with system tray integration
- **Error Recovery**: Comprehensive exception handling with graceful degradation
- **Single Instance**: Enforces one running instance per user session

**Recording Workflow**:
1. Hotkey trigger → Store focused window information
2. Start audio recording → Real-time audio capture
3. Stop recording → Process audio through Whisper AI
4. Focus original window → Paste transcribed text

### State Management (`state_manager.py`)

**Finite State Machine** with four core states:
- **`IDLE`**: Ready for recording, awaiting user input
- **`RECORDING`**: Actively capturing audio from microphone
- **`PROCESSING`**: Transcribing audio using AI model
- **`ERROR`**: Handling failures with recovery mechanisms

**Features**:
- Enforced state transitions with validation
- Recording duration tracking
- PyQt6 signal emission for state changes
- Automatic error recovery

### Audio Processing Pipeline

#### AudioRecorder (`audio_recorder.py`)
- **Technology**: sounddevice with numpy for real-time audio capture
- **Configuration**: 16kHz mono, float32 format (optimized for Whisper)
- **Threading**: Separate recording thread with queue-based data collection
- **Device Management**: Audio device enumeration and automatic selection
- **Performance**: Low-latency streaming with efficient memory usage

#### Transcriber (`transcriber.py`)
- **AI Engine**: faster-whisper (optimized Whisper implementation)
- **Model Management**: Lazy loading with configurable model sizes (tiny, base, small, medium, large)
- **Processing**: Audio normalization → Voice Activity Detection → Transcription
- **Optimization**: CPU-focused with int8 quantization for performance
- **Language Support**: Multi-language with automatic detection

### Hotkey Management Strategies

VoxVibe supports multiple hotkey capture strategies with automatic fallback:

#### DBus Hotkey Manager (Recommended) (`hotkey_manager/dbus_hotkey_manager.py`)
- **Integration**: Works with GNOME Shell extension for system-level shortcuts
- **DBus Service**: Exposes `app.voxvibe.Service` with `TriggerHotkey()` method
- **Advantages**: Native desktop integration, reliable across all applications
- **Platform**: GNOME Shell (X11 and Wayland)

#### Qt Hotkey Manager (Alpha) (`hotkey_manager/qt_hotkey_manager.py`)
- **Technology**: pynput for global hotkey capture
- **Status**: ⚠️ **Alpha quality** - limited compatibility
- **Issues**: Struggles with browser applications that intercept keyboard shortcuts
- **Use Case**: Fallback when DBus/GNOME extension unavailable
- **Configuration**: Default Super+X hotkey (configurable)

### Window Management Strategies

The window manager supports multiple strategies with automatic fallback:

#### DBus Strategy (Preferred) (`window_manager/dbus_strategy.py`)
- **Integration**: Communicates with GNOME Shell extension via DBus
- **Methods**: `GetFocusedWindow()`, `FocusAndPaste(windowId, text)`
- **Window Tracking**: JSON-based window information storage
- **Advantages**: Native GNOME integration, works on both X11 and Wayland
- **Reliability**: Preferred method for all GNOME users


### System Integration

#### System Tray (`system_tray.py`)
- **Framework**: Qt6 QSystemTrayIcon
- **Visual Feedback**: State-based icons (idle, recording, processing)
- **Context Menu**: Recording controls, settings access, service management
- **User Interaction**: Click-to-toggle recording, right-click for menu

#### Single Instance Management (`single_instance.py`)
- **Technology**: QLocalServer for process coordination
- **Lock Management**: Socket-based single instance enforcement
- **Recovery**: Automatic cleanup of stale locks
- **Reset**: Command-line `--reset` flag for manual cleanup

## DBus Interface

### Service Registration
- **Bus**: Session DBus
- **Service Name**: `app.voxvibe.Service`
- **Object Path**: `/app/voxvibe/Service`
- **Interface**: `app.voxvibe.Service`

### Exposed Methods

**`TriggerHotkey()`**
- **Purpose**: External hotkey triggering (called by GNOME extension)
- **Behavior**: Toggles recording state (start/stop)
- **Integration**: Primary interface for GNOME Shell extension

### DBus Communication with GNOME Extension

**Outbound Calls** (Python → Extension):
- **`GetFocusedWindow()`**: Retrieve current window information as JSON
- **`FocusAndPaste(windowId, text)`**: Focus window and paste transcribed text

**Return Formats**:
```json
// GetFocusedWindow() response
{
  "title": "Terminal - user@hostname:~",
  "wm_class": "gnome-terminal-server", 
  "id": 123456
}
```

## Development Environment

### Prerequisites

1. **Python Environment**:
   ```bash
   # Install uv package manager
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install system dependencies
   sudo apt install portaudio19-dev  # Ubuntu/Debian
   sudo dnf install portaudio-devel  # Fedora
   ```

2. **Development Tools**:
   I have mostly used `busctl` to inspect DBus interfaces and `journalctl` to view logs.

### Development Setup

1. **Environment Setup**:
   ```bash
   cd app/
   uv sync                    # Install dependencies
   ```

2. **Run**:
   ```bash
   uv run python -m voxvibe   # Run directly
   ```

### Testing and Debugging

#### Manual Testing

1. **Service Testing**:
   ```bash
   # Run in foreground for debugging
   uv run python -m voxvibe
   
   # Check service status
   systemctl --user status voxvibe.service
   
   # View service logs
   journalctl --user -f -u voxvibe.service
   ```

2. **DBus Interface Testing**:
   ```bash
   # Test hotkey trigger
   busctl call org.gnome.Shell.Extensions.VoxVibe /org/gnome/Shell/Extensions/VoxVibe org.gnome.Shell.Extensions.VoxVibe TriggerHotkey
   
   # Monitor DBus traffic
   dbus-monitor --session "interface='app.voxvibe.Service'"
   ```

3. **Component Testing**:
   ```bash
   # Test audio recording
   python -c "
   from voxvibe.audio_recorder import AudioRecorder
   recorder = AudioRecorder()
   recorder.start_recording()
   # Speak for a few seconds
   data = recorder.stop_recording()
   print(f'Recorded {len(data)} samples')
   "
   
   # Test transcription
   python -c "
   from voxvibe.transcriber import Transcriber
   import numpy as np
   transcriber = Transcriber()
   # Use test audio data
   result = transcriber.transcribe(test_audio)
   print(f'Transcription: {result}')
   "
   ```

#### Strategy Testing

**Window Manager Strategy Testing**:
```bash
python -c "
from voxvibe.window_manager import WindowManager
wm = WindowManager()
print('Available strategies:', [s.get_strategy_name() for s in wm._strategies])
print('Active strategy:', wm.get_active_strategy().get_strategy_name())
wm.store_current_window()
print('Diagnostics:', wm.get_diagnostics())
"
```

**Hotkey Manager Testing**:
```bash
python -c "
from voxvibe.hotkey_manager import HotkeyManagerFactory
manager = HotkeyManagerFactory.create_manager()
print('Hotkey manager:', type(manager).__name__)
print('Available:', manager.is_available())
"
```

### Configuration and Debugging

#### Audio Configuration
```bash
# List audio devices
python -c "
import sounddevice as sd
print('Available audio devices:')
print(sd.query_devices())
"

# Test microphone
python -c "
import sounddevice as sd
import numpy as np
print('Recording test...')
data = sd.rec(int(2 * 16000), samplerate=16000, channels=1)
sd.wait()
print(f'Recorded audio: min={data.min():.3f}, max={data.max():.3f}')
"
```

#### DBus Debugging
```bash
# Check DBus service registration
gdbus introspect --session \
  --dest app.voxvibe.Service \
  --object-path /app/voxvibe/Service

# Monitor all session DBus traffic
dbus-monitor --session
```

#### Logging Configuration
The application uses Python's logging framework. Enable debug logging:
```bash
# Set environment variable
export VOXVIBE_LOG_LEVEL=DEBUG
voxvibe

# Or modify code temporarily
import logging
logging.getLogger('voxvibe').setLevel(logging.DEBUG)
```

### Common Development Tasks

**Reload after code changes**:
```bash
# Kill running service
pkill -f voxvibe

# Reinstall and restart
uv build && uv pip install --force-reinstall dist/*.whl
systemctl --user restart voxvibe.service
```

**Reset stuck instances**:
```bash
voxvibe --reset
```

**Strategy fallback testing**:
```bash
# Disable GNOME extension to test fallbacks
gnome-extensions disable voxvibe@voxvibe.app
voxvibe  # Should fall back to Qt hotkey manager
```

## Performance Considerations

### Resource Usage
- **Memory**: ~50-100MB for base model, ~200-500MB for larger Whisper models
- **CPU**: Transcription uses significant CPU during processing
- **Latency**: ~1-3 seconds for transcription depending on audio length and model size

### Optimization Tips
- Use smaller Whisper models (tiny, base) for faster transcription
- Enable int8 quantization for better performance
- Monitor system resources during development

### Model Management
```python
# Configure transcriber for performance
transcriber = Transcriber(
    model_size="base",      # Balance of speed vs accuracy
    device="cpu",           # Force CPU usage
    compute_type="int8"     # Quantization for speed
)
```

## Troubleshooting

### Common Issues

1. **Audio Recording Fails**:
   - Check microphone permissions
   - Verify PortAudio installation
   - Test with `pavucontrol`

2. **DBus Communication Fails**:
   - Ensure GNOME extension is enabled
   - Check DBus service registration
   - Verify session bus connectivity

3. **Hotkey Not Working**:
   - DBus strategy requires GNOME extension
   - Qt strategy conflicts with browser shortcuts
   - Check for competing applications

4. **Window Focus Issues**:
   - DBus strategy works on X11 and Wayland
   - Some applications block focus changes

### Diagnostic Commands
```bash
# Complete system check
python -c "
from voxvibe.window_manager import WindowManager
from voxvibe.hotkey_manager import HotkeyManagerFactory

wm = WindowManager()
hm = HotkeyManagerFactory.create_manager()

print('=== VoxVibe Diagnostics ===')
print('Window Manager:', wm.get_active_strategy().get_strategy_name())
print('Hotkey Manager:', type(hm).__name__)
print('Window Manager Diagnostics:')
for k, v in wm.get_diagnostics().items():
    print(f'  {k}: {v}')
"
```

## Dependencies

### Core Dependencies
- **PyQt6** (>=6.9.1): GUI framework and service infrastructure
- **faster-whisper** (>=1.1.1): Optimized Whisper AI for transcription
- **sounddevice** (>=0.5.2): Real-time audio I/O
- **numpy** (>=2.3.0): Numerical operations for audio processing

### Optional Dependencies
- **pynput** (>=1.7.6): Global hotkey capture (Qt strategy)
- **psutil** (>=5.9.0): System utilities
- **qt-material** (>=2.17): UI theming

## Future Development

### Planned Enhancements
- GUI settings dialog for configuration
- Multiple language support with language detection
- Voice activity detection improvements
- Real-time transcription display
- Custom wake words and hotkey combinations

### Architecture Extensions
- Plugin system for additional strategies
- Configuration file management
- Advanced audio preprocessing
- Cloud transcription service integration
- WebRTC-based audio processing