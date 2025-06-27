# VoxVibe GNOME Shell Extension

The GNOME Shell extension handles all desktop integration for VoxVibe, providing hotkey registration, window management, and text pasting capabilities. It communicates with the Python application via DBus to orchestrate the complete voice dictation workflow.

## Architecture

The extension acts as a bridge between GNOME Shell's desktop environment and the VoxVibe Python service:

- **Hotkey Management** - Registers `Super+X` global shortcut and triggers Python service
- **Window Tracking** - Monitors focused windows and provides window focus/activation  
- **Text Pasting** - Handles clipboard management and keyboard simulation for text insertion
- **DBus Communication** - Exposes methods for the Python app and calls Python service methods

## DBus Interfaces

### Extension DBus Interface

The extension exposes a DBus service at:
- **Service Name**: `org.gnome.Shell.Extensions.VoxVibe` 
- **Object Path**: `/org/gnome/Shell/Extensions/VoxVibe`
- **Interface**: `org.gnome.Shell.Extensions.VoxVibe`

#### Methods

**`GetFocusedWindow() -> windowInfo`**
- Returns information about the currently focused window as a JSON string
- **Return format:**
  ```json
  {
    "title": "Window Title",
    "wm_class": "ApplicationClass", 
    "id": 123456
  }
  ```
- Returns empty string if no window is focused or window was destroyed

**`FocusAndPaste(windowId, text) -> success`**
- Focuses the specified window and pastes the provided text
- **Parameters:**
  - `windowId` (uint32): Window ID extracted from `GetFocusedWindow()` result
  - `text` (string): Text content to paste
- **Returns:** `success` (boolean) - true if operation succeeded
- **Implementation:**
  1. Searches all window actors for matching window ID
  2. Activates/focuses the target window  
  3. Sets clipboard content (both CLIPBOARD and PRIMARY selections)
  4. Simulates `Ctrl+V` keystroke after 100ms delay

#### Signals

**`WindowFocused(windowInfo)`**
- Emitted whenever window focus changes in GNOME Shell
- **Parameters:**
  - `windowInfo` (string): JSON information about newly focused window
- **Format:** Same JSON structure as `GetFocusedWindow()` return value
- Currently emitted but not consumed by Python app

### Python Service Interface

The extension calls methods on the Python VoxVibe service:
- **Service Name**: `app.voxvibe.Service`
- **Object Path**: `/app/voxvibe/Service`  
- **Interface**: `app.voxvibe.Service`

#### Methods Called

**`TriggerHotkey()`**
- Called when `Super+X` hotkey is pressed
- Triggers the Python service to start/stop recording
- Called asynchronously to prevent GNOME Shell UI blocking

## Settings Schema

The extension uses GSettings for configuration:
- **Schema ID**: `org.gnome.shell.extensions.voxvibe`
- **Schema Path**: `/org/gnome/shell/extensions/voxvibe/`

### Settings Keys

**`launch-hotkey`** (array of strings)
- Default: `['<Super>X']`
- Configurable hotkey combination to trigger voice dictation
- Uses GNOME's standard keybinding format

## Development Environment Setup

### Prerequisites

1. **GNOME Shell Development Tools:**
   ```bash
   sudo apt install gnome-shell-extensions gnome-extensions-app
   # or
   sudo dnf install gnome-extensions-app gnome-shell-extension-*
   ```

2. **DBus Development Tools:**
   ```bash
   sudo apt install d-feet dbus-x11
   # or  
   sudo dnf install d-feet dbus-x11
   ```

### Development Installation

1. **Create development symlink:**
   ```bash
   ln -sf "$(pwd)/extension" ~/.local/share/gnome-shell/extensions/voxvibe@voxvibe.app
   ```

2. **Compile GSettings schema:**
   ```bash
   cd extension
   glib-compile-schemas .
   ```

3. **Install schema globally (optional for development):**
   ```bash
   sudo cp org.gnome.shell.extensions.voxvibe.gschema.xml /usr/share/glib-2.0/schemas/
   sudo glib-compile-schemas /usr/share/glib-2.0/schemas/
   ```

4. **Reload GNOME Shell:**
   - **X11 Session:** `Alt+F2` → type `r` → Enter
   - **Wayland Session:** Log out and log back in

5. **Enable extension:**
   ```bash
   gnome-extensions enable voxvibe@voxvibe.app
   ```

### Development Workflow

#### Testing DBus Interface

Use `d-feet` or command line tools to test DBus methods:

```bash
# Test GetFocusedWindow
dbus-send --session --print-reply \
  --dest=org.gnome.Shell.Extensions.VoxVibe \
  /org/gnome/Shell/Extensions/VoxVibe \
  org.gnome.Shell.Extensions.VoxVibe.GetFocusedWindow

# Test FocusAndPaste  
dbus-send --session --print-reply \
  --dest=org.gnome.Shell.Extensions.VoxVibe \
  /org/gnome/Shell/Extensions/VoxVibe \
  org.gnome.Shell.Extensions.VoxVibe.FocusAndPaste \
  uint32:123456 string:"Hello World"

# Monitor WindowFocused signals
dbus-monitor --session "type='signal',interface='org.gnome.Shell.Extensions.VoxVibe'"
```

#### Debugging

1. **View extension logs:**
   ```bash
   journalctl -f -o cat /usr/bin/gnome-shell
   ```

2. **Examine extension logs:**
   - Extension logs are prefixed with `[VoxVibe]`
   - Use `globalThis.log?.()` for conditional logging

3. **Test hotkey registration:**
   ```bash
   # Check if hotkey is registered
   gsettings get org.gnome.shell.extensions.voxvibe launch-hotkey
   
   # Manually trigger (for testing)
   gdbus call --session \
     --dest app.voxvibe.Service \
     --object-path /app/voxvibe/Service \
     --method app.voxvibe.Service.TriggerHotkey
   ```

#### Common Development Tasks

**Reload extension after code changes:**
```bash
gnome-extensions disable voxvibe@voxvibe.app
gnome-extensions enable voxvibe@voxvibe.app
```

**Validate status:**
```bash
gnome-extensions info voxvibe@voxvibe.app
```

## File Structure

```
extension/
├── extension.js                    # Main extension implementation
├── metadata.json                   # Extension metadata and compatibility
├── org.gnome.shell.extensions.voxvibe.gschema.xml  # GSettings schema
├── gschemas.compiled               # Compiled schema (generated)
└── README.md                       # This file
```

## Key Implementation Details

### Window Management

- Uses `global.get_window_actors()` to enumerate all windows
- Window information includes title, WM class, and native window ID
- Tracks focus changes via `global.display.connect('notify::focus-window')`
- Window activation uses `window.activate(global.get_current_time())`
- Window matching uses native `window.get_id()` for reliable identification

### Keyboard Simulation  

- Uses `Clutter.VirtualDevice` for low-level keyboard event injection
- Simulates `Ctrl+V` by pressing/releasing Control and V keys in sequence
- 100ms delay ensures clipboard content is set before paste simulation

### Clipboard Management

- Sets both `CLIPBOARD` and `PRIMARY` selections for compatibility
- Uses `St.Clipboard.get_default()` for GNOME Shell clipboard access
- Handles text content only (no rich text or media)

### Error Handling

- All DBus methods include try/catch blocks
- Failed operations return appropriate error values (false, empty string)
- Extensive logging for debugging and troubleshooting
- Graceful degradation when windows are destroyed or services unavailable