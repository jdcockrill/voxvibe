<div align="left" style="margin-bottom: 20px;">
  <img src="docs/voxvibe-logo-with-text.svg" alt="VoxVibe Logo" width="730" height="200" style="vertical-align: middle; margin-right: 20px;">
</div>

**Voice dictation that just works.** Press `Super+X` anywhere in GNOME, speak your thoughts, and watch your words appear exactly where you need them.

VoxVibe integrates directly with GNOME providing dictation functionality to any application.

VoxVibe superpowers your Linux workflow with local AI transcription - fast and accurate speech-to-text that works where you are.

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
   ```

2. **Download and run the installer:**
   ```bash
   curl -sSL https://raw.githubusercontent.com/jdcockrill/voxvibe/main/install.sh | bash
   ```

3. **Reload GNOME Shell:**
   - **X11:** Press `Alt+F2`, type `r`, press Enter
   - **Wayland:** Log out and log back in

That's it! Use `Super+X` to start voice dictation.

## Using VoxVibe

### Primary Usage

- **Press `Super+X`**: Start/stop recording (main method)
- **Speak your thoughts**: Audio is captured and transcribed
- **Text appears**: Automatically pasted where you were typing

### System Tray

VoxVibe also runs in the system tray:

- Provides an alternative way to start/stop recording
- Access to settings and profiles
- Access to recent transcriptions that can be copied again

## Configuration

VoxVibe works great with default settings, but you can customize its behavior through a configuration file. The application will automatically create a default configuration file on first run.

### Accessing Settings

The easiest way to modify settings is through the system tray:
1. Click the VoxVibe icon in your system tray
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
- `tiny`, `tiny.en` – Smallest model (~39 M parameters). Fastest (≈3× quicker than `base`) and lowest memory use; suitable for quick voice commands but noticeably less accurate on long or technical sentences.
- `base`, `base.en` – **Default** size (~74 M parameters). Good all-rounder offering real-time dictation speed on most CPUs/GPUs with solid accuracy for everyday language.
- `small`, `small.en`, `distil-small.en` – Medium-sized (~244 M / 122 M distilled). ~3-4 % WER improvement over `base` with ~1.5× slower inference; distilled variant halves memory and recovers much of the speed.
- `medium`, `medium.en`, `distil-medium.en` – Large mid-tier (~769 M / 384 M distilled). Near large-model accuracy while ~2× slower than `small`; GPU recommended for comfortable real-time use.
- `large-v1`, `large-v2`, `large-v3` – Full-size Whisper models (~1.5 B parameters). Highest accuracy but also the slowest and most resource-intensive.
- `distil-large-v2`, `distil-large-v3` – Distilled versions (~50 % fewer parameters). Around 1.7-2× faster than the full large models with only a very small drop in accuracy (≈0.5–1 % WER).
- `large-v3-turbo`, `turbo` – "Turbo" variant of `large-v3` that applies aggressive quantisation and decoder optimisations. Up to 4× faster than `large-v3` while roughly matching the accuracy of the distilled models.

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
strategy = "auto"           # Window management: "auto", "dbus"
paste_delay = 0.1           # Delay before pasting text (seconds)
```

#### Hotkey Management

```toml
[hotkeys]
strategy = "auto"           # Hotkey handling: "auto", "dbus", "qt"
```

**Strategy Options:**
- `"auto"` - Automatically choose best available strategy
- `"dbus"` - Use GNOME extension for global hotkeys (recommended)
- `"qt"` - Use Qt's global hotkey system (fallback)

#### System Tray

```toml
[ui]
startup_delay = 2.0         # Delay before starting services
show_notifications = true   # Show system notifications
minimize_to_tray = true     # Minimize to system tray
```

#### Logging

```toml
[logging]
level = "INFO"              # Log level: "DEBUG", "INFO", "WARNING", "ERROR"
file = "~/.local/share/voxvibe/voxvibe.log"
```

#### Post-Processing

```toml
[post_processing]
enabled = true              # Enable LLM-based text improvement
model = "openai/gpt-4.1-mini"  # LLM model for post-processing
temperature = 0.3           # Temperature for LLM generation
setenv = {}                 # Environment variables for LLM providers
```

VoxVibe includes intelligent post-processing that uses AI to improve transcribed text by:

- Fixing transcription errors and typos
- Improving formatting and readability
- Adding proper punctuation and capitalization
- Converting lists into bullet points when appropriate
- Correcting common speech-to-text errors (homophones, word boundaries)
- Maintaining original meaning and tone

See [Profiles](#profiles) to customize post-processing based on the active application.

### Configuration Tips

- **Most settings work well as defaults** - only change what you need
- **Model size** is the most common setting to adjust based on your hardware and accuracy needs
- Changes take effect after restarting VoxVibe (quit and restart from system tray)
- Invalid configuration values will fall back to defaults
- The configuration file includes helpful comments explaining each option

## History

VoxVibe saves your transcriptions locally for easy access and reuse.

### Accessing History

- **System tray menu**: Recent transcriptions appear in the tray menu
- **Click to copy**: Click any history item to copy it to your clipboard
- **Storage**: Transcriptions are saved to `~/.local/share/voxvibe/history.db`

### Configuration

```toml
[history]
enabled = true              # Store transcription history
max_entries = 20            # Maximum entries to keep
storage_path = "~/.local/share/voxvibe/history.db"
```

## Profiles

Profiles automatically apply custom post-processing prompts based on the active application.

### How Profiles Work

1. When recording starts, VoxVibe detects the focused window
2. Window information is matched against configured regex patterns
3. If a match is found, the profile's custom prompt is used
4. Otherwise, the default post-processing is applied

### Configuration

Edit `~/.config/voxvibe/profiles.toml`:

```toml
# Define a profile
[[profile]]
name = "software_development"
prompt = '''
You are a senior software engineer. Transform voice notes into clear technical content suitable for development environments - whether that's code comments, documentation, commit messages, issue descriptions, or technical discussions. Use precise technical terminology and proper formatting.
'''

# Link profile to applications
[[profile_matcher]]
profile_name = "software_development"
wm_class_matcher = "Code|IntelliJ|Windsurf"
```

### Matching Options

- **`wm_class_matcher`**: Matches application name (e.g., "Code", "Firefox")
- **`title_matcher`**: Matches window title (e.g., "Gmail", "main.py")

Both use regex patterns and are case-insensitive.

### Example Profiles

```toml
# Email formatting
[[profile]]
name = "email"
prompt = "Format as professional email content with proper structure."

[[profile_matcher]]
profile_name = "email"
wm_class_matcher = "Thunderbird|Mail"
title_matcher = "Gmail|Outlook"

# Casual messaging
[[profile]]
name = "casual"
prompt = "Format as casual conversation. Keep tone informal and friendly."

[[profile_matcher]]
profile_name = "casual"
title_matcher = "WhatsApp|Discord|Slack"
```

### Managing Profiles

- **Edit**: Modify `~/.config/voxvibe/profiles.toml` directly or use the system tray "Profiles" menu
- **Debug**: Enable debug logging to see which profiles match for each window
- **Reload**: Restart VoxVibe to apply profile changes

## Architecture

VoxVibe has two main components:

```text
┌─────────────────────────────┐         ┌─────────────────────────────┐
│      GNOME Extension        │         │      Python Service         │
│     (extension.js)          │◄────────┤       (voxvibe)             │
│                             │  DBus   │                             │
│ • Global hotkey capture     │         │ • Audio recording           │
│ • System tray indicator     │         │ • Speech transcription      │
│ • Window focus tracking     │         │ • Post-processing           │
│ • Text pasting              │         │ • History storage           │
└─────────────────────────────┘         │ • State management          │
                                        └─────────────────────────────┘
```

### Components

**GNOME Extension**: Handles desktop integration including global hotkeys, system tray, window tracking, and text pasting.

**Python Service**: Manages audio recording, transcription, post-processing, and history storage. Runs as a background service.

**Data Flow:**
1. Hotkey pressed → Extension signals Python service
2. Python service captures focused window and starts recording
3. Audio is recorded and transcribed using Whisper
4. Text is post-processed and saved to history
5. Extension pastes text to the original window

### Why Two Components?

The split architecture was chosen for reliability and cross-compatibility:

- **Reliable Keyboard Shortcuts:** The GNOME extension provides a robust way to capture global hotkeys (`Super+X`) that works consistently across the desktop. Python libraries for this can be unreliable with different window managers.
- **Wayland & X11 Compatibility:** By letting the GNOME extension handle window interactions, we get a single solution that works for both Wayland and X11 display servers.
- **Focus on Strengths:** Each component does what it's best at. The extension handles deep GNOME integration, while the Python application manages audio processing and AI transcription.

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

### Contributions

A special thanks to the following people for their contributions:

- **[dkh99](https://github.com/dkh99):** For significant contributions to the design of the user experience.

### Release

To release a new version, follow these steps:

1.  **Update Version:** Update the version in `app/pyproject.toml` and `extension/metadata.json`.
2.  **Build Release:** Run `make release` to create the release package.
3.  **Push Release:** Push the release tag to GitHub: `git push origin v$(VERSION)`.
