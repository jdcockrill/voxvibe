# VoxVibe

**Voice dictation that just works.** Press `Super+X` anywhere in GNOME, speak your thoughts, and watch your words appear exactly where you need them.

VoxVibe seamlessly integrates into your Linux workflow with local AI transcription - fast and accurate speech-to-text that works where you are.

Built with [Claude Code](https://www.anthropic.com/claude-code) and [Windsurf](https://windsurf.com/).

## Installation

1. **Install system dependencies:**
   ```bash
   # Ubuntu/Debian
   sudo apt install -y portaudio19-dev pipx
   
   # Fedora
   sudo dnf install portaudio portaudio-devel pipx
   # Fedora users also need AppIndicator extension for system tray:
   # https://github.com/ubuntu/gnome-shell-extension-appindicator
   
   # Arch Linux
   sudo pacman -S portaudio python-pipx
   ```

2. **Download and run the installer:**
   ```bash
   curl -sSL https://raw.githubusercontent.com/jdcockrill/voxvibe/main/install.sh | bash
   ```

3. **Reload GNOME Shell:**
   - **X11:** Press `Alt+F2`, type `r`, press Enter
   - **Wayland:** Log out and log back in

That's it! Use `Super+X` to start voice dictation.

## Configuration

VoxVibe works great with default settings, but you can customize its behavior through a configuration file. The application will automatically create a default configuration file on first run.

### Accessing Settings

The easiest way to modify settings is through the system tray:
1. Right-click the VoxVibe microphone icon in your system tray
2. Select **Settings** from the menu
3. Your default text editor will open the configuration file

Alternatively, you can directly edit the configuration file located at:
- `~/.config/voxvibe/config.toml`

### Configuration Options

The configuration file uses the [TOML](https://toml.io) format and is organized into sections:

#### Transcription Settings
```toml
[transcription]
model = "base"              # Whisper model size (see options below)
language = "en"             # Language code or "auto" for auto-detection  
device = "auto"             # Processing device: "auto", "cpu", or "cuda"
compute_type = "auto"       # Precision: "auto", "int8", "int16", "float16", "float32"
```

**Model Options** (from fastest/least accurate to slowest/most accurate):
- `tiny`, `tiny.en` - Fastest, good for simple dictation
- `base`, `base.en` - **Default** - Good balance of speed and accuracy
- `small`, `small.en` - More accurate, slightly slower
- `medium`, `medium.en` - High accuracy, moderate speed
- `large-v1`, `large-v2`, `large-v3` - Highest accuracy, slower

For most users, `base` provides the best balance. Use `small` or `medium` if you need higher accuracy and don't mind slower processing.

#### Audio Settings
```toml
[audio]
sample_rate = 16000         # Audio sample rate (16kHz recommended)
channels = 1                # Mono (1) or stereo (2) recording
```

#### User Interface
```toml
[ui]
startup_delay = 2.0         # Delay before starting services
show_notifications = true   # Show system notifications
minimize_to_tray = true     # Minimize to system tray
```

#### Window Management
```toml
[window_manager]
strategy = "auto"           # Window management: "auto", "dbus", "xdotool"
paste_delay = 0.1           # Delay before pasting text (seconds)
```

#### Hotkey Management  
```toml
[hotkeys]
strategy = "auto"           # Hotkey handling: "auto", "dbus", "qt"
```

#### Logging
```toml
[logging]
level = "INFO"              # Log level: "DEBUG", "INFO", "WARNING", "ERROR"
file = "~/.local/share/voxvibe/voxvibe.log"
```

### Configuration Tips

- **Most settings work well as defaults** - only change what you need
- **Model size** is the most common setting to adjust based on your hardware and accuracy needs
- Changes take effect after restarting VoxVibe (quit and restart from system tray)
- Invalid configuration values will fall back to defaults
- The configuration file includes helpful comments explaining each option

## Architecture

VoxVibe consists of two main components that communicate via DBus:

```text
┌─────────────────────────────┐         ┌─────────────────────────────┐
│      GNOME Extension        │         │      Python Application     │
│     (extension.js)          │◄────────┤       (voxvibe)             │
│                             │  DBus   │                             │
│ • Captures hotkey           │         │ • Audio recording           │
│ • Tracks focused windows    │         │ • Speech transcription      │
│ • Pastes text via clipboard │         │ • Service orchestration     │
│ • System tray indicator     │         │ • Window management         │
└─────────────────────────────┘         └─────────────────────────────┘
```

**Data Flow:**
1. **Hotkey Trigger** → Extension captures keyboard shortcut and signals Python app
2. **Window Tracking** → Python app requests current focused window ID from extension  
3. **Audio Processing** → Python app records and transcribes speech independently
4. **Text Pasting** → Python app sends transcribed text back to extension for pasting

**GNOME Extension** handles all desktop integration:
- Registers global keyboard shortcuts
- Maintains window focus tracking
- Provides system tray presence
- Simulates text pasting via clipboard + Ctrl+V

**Python Application** handles all AI processing:
- Captures audio from microphone
- Transcribes speech using Whisper AI
- Orchestrates the complete workflow
- Communicates with extension via DBus

### Why Two Components?

The split architecture (Python backend + GNOME Shell extension) was chosen for reliability and cross-compatibility:

- **Reliable Keyboard Shortcuts:** The GNOME extension provides a robust way to capture global hotkeys (`Super+X`) that works consistently across the desktop. Python libraries for this (like `pynput` or `keyboard`) can be unreliable, especially with different window managers.
- **Wayland & X11 Compatibility:** By letting the GNOME extension handle window interactions (like pasting text), we get a single solution that works for both Wayland and X11 display servers. This avoids writing and maintaining separate, complex code for each.
- **Focus on Strengths:** Each component does what it's best at. The extension handles deep GNOME integration, while the Python application manages the heavy lifting of audio processing and AI transcription.

## Development

### Directory Structure

```text
voxvibe/
├── app/         # Python transcription app (source, pyproject.toml)
├── extension/   # GNOME Shell extension (extension.js, metadata.json)
├── README.md    # This file
```

---

For further development details on specific components, you can explore their respective directories.
The `app/README.md` can be used for more detailed notes on Python app development, and `extension/README.md` for extension-specific development notes.

### Credits

A special thanks to the following people for their contributions:

- **[dkh99](https://github.com/dkh99):** For significant contributions to the design of the user experience.

### Release

To release a new version, follow these steps:

1.  **Update Version:** Update the version in `app/pyproject.toml` and `extension/metadata.json`.
2.  **Build Release:** Run `make release` to create the release package.
3.  **Push Release:** Push the release tag to GitHub: `git push origin v$(VERSION)`.
