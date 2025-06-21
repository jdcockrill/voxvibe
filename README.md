# VoxVibe v0.2.0 🎤

**Fast, reliable voice transcription with global hotkeys for Linux**

VoxVibe is a unified Python application that provides instant speech-to-text transcription with global hotkeys. Simply hold **Win+Alt** and speak - VoxVibe will transcribe your speech and paste it directly where you need it.

## ✨ Features

- **🚀 Ultra-fast pasting** (0.25s response time)
- **🎯 Global hotkeys** - Works anywhere in the system
- **📚 Transcription history** - Access recent transcriptions via tray menu  
- **🔄 Auto-startup** - Runs automatically when you log in
- **🖥️ Native Wayland & X11 support** - Works on any Linux desktop
- **🎨 Clean system tray integration** - Unobtrusive background operation

## 🎯 Quick Start

1. **Clone and install:**
   ```bash
   git clone <repository-url>
   cd voxvibe
   make all
   ```

2. **Start using immediately:**
   - VoxVibe will auto-start and appear in your system tray
   - Hold **Win+Alt** and speak to transcribe
   - Text appears instantly where your cursor is

## 📋 Prerequisites

### Required Dependencies

1. **Python 3.11+** - Check with `python3 --version`
2. **uv** - Fast Python package manager
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **PortAudio** - For audio recording
   ```bash
   # Ubuntu/Debian
   sudo apt install -y portaudio19-dev
   
   # Fedora
   sudo dnf install portaudio portaudio-devel
   
   # Arch Linux
   sudo pacman -S portaudio
   ```

### Wayland Support (Recommended)

For optimal Wayland compatibility, install **ydotool**:
```bash
# Ubuntu/Debian  
sudo apt install ydotool

# Fedora
sudo dnf install ydotool

# Arch Linux
sudo pacman -S ydotool
```

**Note:** ydotool requires setup - see [Wayland Setup](#wayland-setup) section below.

## 🔧 Installation

### Automatic Installation (Recommended)

The simplest way to install VoxVibe:

```bash
# Clone the repository
git clone <repository-url>
cd voxvibe

# Install everything
make all
```

This will:
- ✅ Set up Python environment with `uv`
- ✅ Install VoxVibe system-wide
- ✅ Configure auto-startup 
- ✅ Set up system tray integration

### Manual Installation

If you prefer manual control:

```bash
# 1. Setup Python environment
cd app
uv sync

# 2. Build the application  
uv build

# 3. Install globally (choose one option)

# Option A: Using pipx (recommended for system-wide installation)
pipx install dist/voxvibe-*.whl

# Option B: Development mode (runs from source)
# No additional installation needed

# 4. Set up autostart

# For pipx installation:
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/voxvibe.desktop << EOF
[Desktop Entry]
Type=Application
Name=VoxVibe
Comment=Voice transcription with global hotkeys
Exec=voxvibe
Icon=microphone
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Categories=AudioVideo;Audio;
EOF
chmod +x ~/.config/autostart/voxvibe.desktop

# For development mode:
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/voxvibe.desktop << EOF
[Desktop Entry]
Type=Application
Name=VoxVibe
Comment=Voice transcription with global hotkeys
Exec=bash -c "cd /path/to/your/voxvibe/app && uv run python -m voxvibe"
Path=/path/to/your/voxvibe/app
Icon=microphone
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Categories=AudioVideo;Audio;
EOF
chmod +x ~/.config/autostart/voxvibe.desktop
```

**Note:** Replace `/path/to/your/voxvibe/app` with your actual installation path.

## ⚙️ System Setup

### Wayland Setup

For Wayland systems, configure ydotool:

```bash
# Enable ydotool service
sudo systemctl enable --now ydotool

# Add yourself to input group (may require logout)
sudo usermod -a -G input $USER

# Test ydotool works
ydotool key ctrl+c
```

### Verify Installation

Check that everything is working:

```bash
# Check VoxVibe is installed
voxvibe --version

# Check dependencies
~/check-voxvibe-conflicts.sh  # (created during installation)
```

## 🎮 Usage

### Basic Operation

1. **Start VoxVibe** - It starts automatically on login, or run `voxvibe`
2. **Look for tray icon** - VoxVibe appears in your system tray
3. **Hold Win+Alt and speak** - Release when done speaking
4. **Text appears instantly** - Transcribed text is pasted where your cursor is

### Hotkeys

| Hotkey | Action |
|--------|--------|
| **Win+Alt** (hold) | Record and transcribe speech |
| **Alt+Space** (hold) | Alternative recording hotkey |
| **Win+Alt+Space** | Toggle hands-free mode |
| **Space** | Exit hands-free mode |

### Tray Menu Features

- **📚 Paste from History** - Access your last 15 transcriptions
- **⭐ Last Transcription** - Quickly re-paste the most recent text
- **ℹ️ About** - View version and hotkey information
- **❌ Quit** - Exit VoxVibe

### History Access

- **Recent transcriptions** appear in the tray menu
- **Double-click tray icon** to paste the last transcription
- **Right-click** for full history menu with timestamps

## 🔧 Management

### Start/Stop VoxVibe

```bash
# Manual start
voxvibe

# Stop (from tray menu or)
pkill voxvibe

# Check if running
ps aux | grep voxvibe
```

### Disable Auto-start

```bash
# Disable auto-start
rm ~/.config/autostart/voxvibe.desktop

# Re-enable auto-start
make all  # (re-run installation)
```

### Check for Conflicts

If you experience issues:

```bash
# Run conflict checker (created during installation)
~/check-voxvibe-conflicts.sh

# This will show:
# - Running VoxVibe processes
# - Old extension conflicts  
# - Installation status
```

## 🛠️ Troubleshooting

### Common Issues

**VoxVibe doesn't start on login:**
```bash
# Check autostart file exists
ls -la ~/.config/autostart/voxvibe.desktop

# Recreate if missing
make all
```

**No audio recording:**
```bash
# Check PortAudio installation
python3 -c "import sounddevice; print('PortAudio OK')"

# Install if needed (see Prerequisites)
```

**Pasting doesn't work on Wayland:**
```bash
# Check ydotool is running
systemctl status ydotool

# Install and configure ydotool (see Wayland Setup)
```

**Multiple tray icons:**
```bash
# Clean up conflicts
~/check-voxvibe-conflicts.sh

# Kill duplicate processes
pkill voxvibe
voxvibe  # Start fresh
```

### Getting Help

1. **Check the conflict detector:** `~/check-voxvibe-conflicts.sh`
2. **View logs:** VoxVibe shows detailed logs when run from terminal
3. **Verify dependencies:** Ensure PortAudio and ydotool are properly installed

## 🏗️ Development

### Project Structure
```
voxvibe/
├── app/                 # Main Python application
│   ├── voxvibe/        # Source code
│   ├── pyproject.toml  # Dependencies and metadata
│   └── README.md       # Development notes
├── extension/          # Legacy GNOME extension (deprecated)
├── Makefile           # Build and installation automation
└── README.md          # This file
```

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd voxvibe/app

# Setup development environment  
uv sync

# Run in development mode
uv run python -m voxvibe

# Install development version
make all
```

### Building Releases

```bash
# Update version in app/pyproject.toml
# Then build and release
make release
```

## 📝 What's New in v0.2.0

### Major Changes
- **🔄 Unified Architecture** - No more GNOME extension required
- **⚡ Improved Performance** - Faster startup and transcription
- **🎯 Enhanced Hotkeys** - More reliable key detection
- **📱 Better Tray Integration** - Cleaner system tray experience
- **🔧 Auto-startup** - Automatic system startup configuration
- **🛠️ Conflict Detection** - Built-in tools to prevent installation issues

### Breaking Changes
- **Removed GNOME extension dependency** - VoxVibe is now a single Python application
- **New installation method** - Use `make all` instead of separate component installation
- **Updated hotkeys** - Simplified to Win+Alt (old shortcuts still work)

---

**Enjoy ultra-fast voice transcription with VoxVibe! 🚀**

For issues or feature requests, please visit the project repository.
