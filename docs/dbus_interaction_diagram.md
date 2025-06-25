# VoxVibe – GNOME Shell Extension DBus Interaction (Hotkey + Window Manager)

```mermaid
sequenceDiagram
    participant User
    participant GNOME_Ext as GNOME Extension (extension.js)
    participant Python_Service as Python VoxVibe Service (service.py)
    participant DBus_Hotkey as DBusHotkeyManager
    participant WindowMgr as WindowManager (DBusWindowManagerStrategy)

    %% --- HOTKEY FLOW ---
    User->>GNOME_Ext: Press Super+X hotkey
    GNOME_Ext->>GNOME_Ext: _onHotkey()
    GNOME_Ext->>Python_Service: org.freedesktop.DBus call → TriggerHotkey()
    Python_Service->>DBus_Hotkey: Dispatch to DBusHotkeyManager.TriggerHotkey()
    DBus_Hotkey-->>Python_Service: emit hotkey_pressed
    Python_Service->>Python_Service: _toggle_recording() via StateManager

    %% --- RECORDING START WORKFLOW ---
    Python_Service->>WindowMgr: store_current_window()
    WindowMgr->>GNOME_Ext: GetFocusedWindow()
    GNOME_Ext-->>WindowMgr: window_id

    %% --- RECORDING STOP & TRANSCRIBE ---
    Python_Service->>Python_Service: Stop recording & transcribe audio
    Python_Service-->>User: (speech → text result)

    %% --- PASTE BACK TO WINDOW ---
    Python_Service->>WindowMgr: focus_and_paste(text)
    WindowMgr->>GNOME_Ext: FocusAndPaste(window_id, text)
    GNOME_Ext->>GNOME_Ext: Focus target window
    GNOME_Ext->>GNOME_Ext: Set clipboard & simulate Ctrl+V
    GNOME_Ext-->>WindowMgr: success/failure
    WindowMgr-->>Python_Service: success/failure

    %% --- OPTIONAL SIGNALS ---
    GNOME_Ext-->>Python_Service: WindowFocused(window_id) [signal]
```

## Description
1. **Hotkey Trigger** – The user presses *Super + X*. The GNOME extension captures this and asynchronously invokes the Python service’s `TriggerHotkey` DBus method.
2. **Recording Toggle** – `DBusHotkeyManager` inside the Python service emits `hotkey_pressed`, which the service maps to `_toggle_recording()`.
3. **Window Tracking** – When recording starts, the service asks the window-manager strategy (DBus) to remember the current focused window via `GetFocusedWindow`.
4. **Transcription** – After the user stops speaking, audio is transcribed inside the Python service.
5. **Paste Back** – The service sends the text back to the previously focused window through the extension’s `FocusAndPaste` method. The extension focuses the window, sets the clipboard content, and simulates paste.
6. **Signals** – The extension continually emits `WindowFocused` to inform the service of focus changes (not yet consumed but available).

This diagram reflects the interaction **when only the DBus hotkey manager and DBus window manager strategy are enabled**.
