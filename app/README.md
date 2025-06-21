# VoxVibe v0.2 - Enhanced Voice Transcription

VoxVibe is a powerful voice dictation application for Linux with global hotkeys, persistent floating UI, and intelligent transcription history.

## ✨ Features

### 🎯 Global Hotkeys
- **Alt+Space**: Hold to talk (quick dictation)
- **Win+Alt**: Hold to talk (alternative combo)  
- **Win+Alt+Space**: Hands-free mode (toggle on/off)
- **Space**: Exit hands-free mode

### 🎤 Persistent Mic Bar
- Always-visible floating microphone bar
- Live waveform visualization during recording
- Drag to reposition anywhere on screen
- Subtle pulsing animation when idle

### 🔊 Audio Feedback
- Pleasant "ping" sound when recording starts
- Confirmation tone when recording stops
- Synthesized tones generated automatically

### 📚 Transcription History
- Automatic storage of last 50 transcriptions
- System tray quick-paste of recent entries
- SQLite database for reliable persistence
- Search and recovery functionality

### 🖥️ System Integration
- GNOME Shell extension for seamless window focus
- System tray icon with quick actions
- Background operation (no main window)
- Wayland and X11 compatibility

## 🚀 Quick Start

### Installation
```bash
# From the repository root
make install
```

### Running
```bash
# Start VoxVibe (runs in background)
voxvibe

# Or run in development mode
cd app/
uv run python -m voxvibe.main
```

### Usage
1. **Quick dictation**: Hold `Alt+Space`, speak, release to paste
2. **Hands-free mode**: Press `Win+Alt+Space` to start continuous recording, press `Space` to stop
3. **Access history**: Right-click the system tray icon
4. **Toggle mic bar**: Middle-click the tray icon or use the context menu

## 🛠️ Development

### Key Dependencies
- **PyQt6**: GUI framework and multimedia support
- **faster-whisper**: Efficient speech-to-text transcription  
- **pynput**: Global hotkey detection
- **sounddevice**: Real-time audio capture
- **qt-material**: Modern dark theme

### Development Commands
```bash
cd app/

# Install dependencies
uv sync

# Run tests
python test_voxvibe.py

# Run linters  
uv run ruff check

# Build package
uv build
```

### Architecture
- **hotkey_service.py**: Global keyboard monitoring and mode management
- **mic_bar.py**: Persistent floating UI with waveform visualization
- **sound_fx.py**: Audio feedback system with synthesized tones
- **history.py**: SQLite-based transcription storage and retrieval
- **tray_icon.py**: System tray integration with quick actions
- **main.py**: Application orchestration and component integration

## 🎛️ Configuration

VoxVibe stores data in standard Linux locations:
- **History database**: `~/.cache/voxvibe/history.sqlite`
- **Sound effects**: `app/voxvibe/sounds/`
- **Logs**: Console output (can be redirected)

## 🐛 Troubleshooting

### Common Issues
- **No sound effects**: Requires PyQt6-Multimedia and numpy
- **Hotkeys not working**: Check pynput permissions and accessibility settings
- **DBus errors**: Ensure GNOME Shell extension is enabled
- **Audio issues**: Verify sounddevice can access your microphone

### Debug Mode
```bash
# Run with verbose output
PYTHONPATH=. python -m voxvibe.main
```

## 📝 Changelog

### v0.2.0 - Enhanced UX Release
- ✅ Multiple global hotkey combinations
- ✅ Persistent floating mic bar with waveform
- ✅ Audio feedback (start/stop pings) 
- ✅ Transcription history with system tray access
- ✅ Hands-free recording mode
- ✅ Drag-to-reposition mic bar
- ✅ Background operation with tray icon

### v0.1.0 - Initial Release  
- Basic voice transcription
- GNOME Shell integration
- Simple Qt UI

For full installation instructions, see the main `README.md` in the repository root.
