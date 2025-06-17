# VoxVibe Development Guide for Claude Code

## Project Overview

**VoxVibe** is a voice dictation application for Linux that enables users to capture audio via keyboard shortcut and paste transcribed text into the previously focused application. The project consists of two main components:

1. **Python Application** (`app/`) - Qt6-based transcription app using Whisper AI
2. **GNOME Shell Extension** (`extension/`) - JavaScript extension for window management and text pasting

## Technology Stack

- **Python**: 3.11+ with PyQt6 for GUI
- **AI/ML**: faster-whisper for speech-to-text transcription  
- **Audio**: sounddevice for audio recording
- **Desktop Integration**: GNOME Shell extension with DBus communication
- **Package Management**: uv (fast Python package manager)
- **Build System**: Enhanced Makefile with distribution and CI/CD support
- **CI/CD**: GitHub Actions for automated builds and releases
- **Documentation**: Comprehensive contributing guidelines and changelog

## Project Structure

```
voxvibe/
├── README.md                    # Main project documentation
├── LICENSE                      # MIT License
├── CONTRIBUTING.md              # Development and contribution guidelines
├── CHANGELOG.md                 # Version history and release notes
├── Makefile                     # Enhanced build system with CI/CD support
├── .github/workflows/           # GitHub Actions CI/CD
│   └── build-and-release.yml   # Automated build and release workflow
├── app/                         # Python transcription application
│   ├── README.md               # App-specific documentation
│   ├── app-description.md      # Detailed app description
│   ├── pyproject.toml          # Python project configuration (v0.0.1)
│   ├── uv.lock                 # Lock file for dependencies
│   ├── mise.toml               # Tool version management
│   ├── dist/                   # Build artifacts (wheels)
│   ├── scripts/                # Development scripts
│   │   └── test_gnome_extension.py
│   └── voxvibe/                # Main Python package
│       ├── __init__.py
│       ├── __main__.py
│       ├── main.py             # Application entry point
│       ├── audio_recorder.py   # Audio capture functionality
│       ├── transcriber.py      # Whisper AI integration
│       ├── dbus_window_manager.py  # GNOME extension communication
│       └── window_manager.py   # Window management utilities
└── extension/                  # GNOME Shell extension
    ├── README.md              # Extension-specific documentation
    ├── metadata.json          # Extension metadata
    └── extension.js           # Main extension logic
```

## Key Components

### Python Application (`app/voxvibe/`)

**Entry Point**: `main.py`
- Qt6-based GUI with recording interface
- Handles audio recording, transcription, and window management
- Integrates with GNOME extension via DBus

**Core Modules**:
- `audio_recorder.py`: Audio capture using sounddevice (16kHz, mono)
- `transcriber.py`: Whisper AI transcription with faster-whisper
- `dbus_window_manager.py`: DBus client for GNOME extension communication
- `window_manager.py`: Window focus and management utilities

**Dependencies** (from `pyproject.toml`):
- `faster-whisper>=1.1.1` - Efficient Whisper AI implementation
- `numpy>=2.3.0` - Numerical operations
- `pyqt6>=6.9.1` - GUI framework
- `sounddevice>=0.5.2` - Audio recording

### GNOME Shell Extension (`extension/`)

**Files**:
- `extension.js`: Main extension logic with DBus interface
- `metadata.json`: Extension metadata (UUID: `voxvibe@voxvibe.app`)

**Features**:
- Tracks focused windows before VoxVibe launches
- Provides DBus interface for window focusing and text pasting
- System tray indicator with microphone icon
- Simulates keyboard input (Ctrl+V) for pasting

## Development Commands

### Enhanced Makefile Commands (from project root)

**Development Commands:**
```bash
# Complete setup - installs both components
make all

# Python app only - sync dependencies and build
make app

# Install Python app wheel
make install

# GNOME extension only - copy files and enable
make extension

# Run linters with validation
make lint

# Clean build artifacts and installations
make clean
```

**Distribution Commands:**
```bash
# Create distribution packages
make dist

# Create complete release package with installation script
make package

# Tag and prepare release (requires clean working tree)
make release

# Show help with all available commands
make help
```

**Utility Commands:**
```bash
# Verify required tools are installed
make check-tools

# Display version information from pyproject.toml and git
make check-version
```

### Python Development (from `app/` directory)

```bash
# Install dependencies
uv sync

# Run application directly
uv run python -m voxvibe

# Run linters
uv run ruff check

# Build wheel package
uv build

# Install built package
uv pip install --force-reinstall dist/*.whl
```

### Extension Development

```bash
# Manual installation
mkdir -p ~/.local/share/gnome-shell/extensions/voxvibe@voxvibe.app
cp -r extension/* ~/.local/share/gnome-shell/extensions/voxvibe@voxvibe.app/

# Enable extension
gnome-extensions enable voxvibe@voxvibe.app

# Reload GNOME Shell (X11 only)
Alt+F2, type 'r', press Enter
```

For Wayland, you need to log out and log in again.

## Architecture & Communication Flow

1. **User triggers** VoxVibe via keyboard shortcut
2. **DBus communication** stores currently focused window ID
3. **Qt6 GUI** launches with recording interface
4. **Audio recording** starts using sounddevice
5. **Whisper transcription** processes audio when recording stops
6. **GNOME extension** refocuses original window and pastes text
7. **Application exits** after successful paste

### DBus Interface

**Service**: `org.gnome.Shell.Extensions.VoxVibe`
**Object Path**: `/org/gnome/Shell/Extensions/VoxVibe`

**Methods**:
- `GetFocusedWindow()` → returns window ID
- `FocusAndPaste(windowId, text)` → focuses window and pastes text

## Configuration Files

### `app/pyproject.toml`
- Python project configuration
- Dependencies and build settings
- Entry point: `voxvibe = "voxvibe.main:main"`

### `app/mise.toml`
- Tool version management
- Python 3.13.4, uv 0.7.13

### `extension/metadata.json`
- Extension UUID: `voxvibe@voxvibe.app`
- GNOME Shell version compatibility: 48
- Extension name and description

## Development Workflow

### Setting Up Development Environment

1. **Clone and navigate**:
   ```bash
   cd $HOME/code/voice-flow
   ```

2. **Verify tools and install everything**:
   ```bash
   make check-tools  # Verify required tools
   make all          # Complete setup
   ```

3. **Create keyboard shortcut**:
   - Open GNOME Settings → Keyboard → Custom Shortcuts
   - Add shortcut: Command `voxvibe`, assign hotkey (e.g., Ctrl+Alt+V)

### Making Changes

1. **Python app changes**:
   ```bash
   cd app
   # Make changes to voxvibe/* files
   uv sync  # if dependencies changed
   uv build && uv pip install --force-reinstall dist/*.whl
   ```

2. **Extension changes**:
   ```bash
   # Make changes to extension/extension.js
   make extension  # reinstall extension
   # Reload GNOME Shell or log out/in
   ```

3. **Run linters and validation**:
   ```bash
   make lint         # Enhanced linting with metadata validation
   make check-version # Check current version info
   ```

### Distribution and Release Workflow

1. **Create distribution build**:
   ```bash
   make dist  # Creates clean build with linting
   ```

2. **Create release package**:
   ```bash
   make package  # Creates complete release tarball with install script
   ```

3. **Prepare and tag release**:
   ```bash
   # Update version in app/pyproject.toml
   # Update CHANGELOG.md
   make release  # Tags version and creates release package
   git push origin main
   git push origin v0.0.1  # Triggers GitHub Actions release
   ```

## Testing

### Local Testing
- **Python app**: Run directly with `uv run python -m voxvibe`
- **Extension**: Use `scripts/test_gnome_extension.py` for testing
- **Integration**: Test full workflow with keyboard shortcut
- **Build validation**: Use `make dist` to test complete build process
- **Release testing**: Use `make package` to test release package creation

### Automated Testing
- **GitHub Actions**: Automatically runs on pull requests and releases
- **CI Pipeline**: Includes linting, building, and artifact creation
- **Release Pipeline**: Automatic GitHub releases when version tags are pushed

### Contributing Workflow
- See `CONTRIBUTING.md` for detailed branching strategy and PR process
- Use conventional commit format for clear change tracking
- Follow semantic versioning guidelines in `CHANGELOG.md`

## Common Issues & Solutions

1. **Extension not loading**: Check GNOME Shell logs with `journalctl -f`
2. **Audio recording fails**: Verify microphone permissions and sounddevice setup
3. **DBus communication fails**: Ensure extension is enabled and GNOME Shell is reloaded
4. **Whisper model loading**: First run downloads model to `~/.cache/whisper`

## Future Development Areas

- GUI settings dialog for configuration
- Multiple language support
- Voice activity detection improvements
- Better Wayland compatibility
- Real-time transcription display
- Custom wake words/hotkeys

## Build and Release System

### Enhanced Makefile Features
- **Tool validation**: `make check-tools` verifies all required dependencies
- **Version management**: Automatic version extraction from `pyproject.toml`
- **Distribution builds**: `make dist` creates clean, linted packages
- **Release packaging**: `make package` creates complete release tarballs with install scripts
- **Git integration**: Automatic tagging and release preparation with `make release`

### GitHub Actions CI/CD
- **Automated testing**: Runs on all pull requests with linting and build validation
- **Automated releases**: Triggered by version tags (e.g., `v0.0.1`)
- **Artifact generation**: Creates both Python wheels and complete release packages
- **Release notes**: Auto-generated with installation instructions

### Contributing Guidelines
- **Branching strategy**: Git Flow-inspired with feature branches
- **Conventional commits**: Structured commit messages for clear change tracking
- **Semantic versioning**: Proper version management following SemVer
- **Documentation**: Comprehensive changelog and contributing guidelines

## Git Information

- **Current Branch**: `2-improve-makefile-or-create-an-install-script`
- **Main Branch**: `main`
- **Recent Commits**: Enhanced build system with CI/CD support
- **Version**: `0.0.1` (from `app/pyproject.toml`)
- **Repository Status**: Enhanced with distribution and release capabilities

## License

MIT License - see LICENSE file for details.