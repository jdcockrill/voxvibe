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
   # Download latest release
   curl -L https://github.com/jamiecockrill/voice-flow/releases/latest/download/voxvibe-installer.tar.gz | tar -xz
   cd voxvibe-installer
   ./install.sh
   ```

3. **Reload GNOME Shell:**
   - **X11:** Press `Alt+F2`, type `r`, press Enter
   - **Wayland:** Log out and log back in

That's it! Use `Super+X` to start voice dictation.

## Architecture

VoxVibe consists of two main components that communicate via DBus:

```
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

```
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
