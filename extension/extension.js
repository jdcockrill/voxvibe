// extension.js - GNOME Extension for Dictation App Window Management
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

import Clutter from 'gi://Clutter';
import St from 'gi://St';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

/**
 * @class DictationWindowExtension
 * @extends Extension
 * @property {Meta.Window|null} _lastFocusedWindow - The last focused GNOME window (Meta.Window or null)
 * @property {Gio.DBusExportedObject|null} _dbusImpl - The exported DBus object for this extension (Gio.DBusExportedObject or null)
 * @property {number|undefined} _focusSignal - Signal handler ID returned by global.display.connect (number or undefined)
 */
export default class DictationWindowExtension extends Extension {
    enable() {
        this._lastFocusedWindow = null;
        this._dbusImpl = null;
        this._setupDBusService();
        this._connectSignals();

        // Add panel indicator with microphone icon (native, no tooltip)
        this._trayButton = new PanelMenu.Button(0.0, 'VoxVibe Indicator', false);
        const icon = new St.Icon({
            icon_name: 'audio-input-microphone-symbolic',
            style_class: 'system-status-icon',
        });
        this._trayButton.add_child(icon);
        // Add menu item showing app name and version (non-interactive)
        const appInfoItem = new PopupMenu.PopupMenuItem('VoxVibe v1');
        appInfoItem.setSensitive(false);
        this._trayButton.menu.addMenuItem(appInfoItem);
        
        // Add separator
        this._trayButton.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        
        // Add history menu item
        const historyItem = new PopupMenu.PopupMenuItem('View history');
        historyItem.connect('activate', () => this._showHistoryPopover());
        this._trayButton.menu.addMenuItem(historyItem);
        
        Main.panel.addToStatusArea('voxvibe-indicator', this._trayButton);
    }

    disable() {
        if (this._dbusImpl) {
            this._dbusImpl.unexport();
            this._dbusImpl = null;
        }
        if (this._focusSignal) {
            global.display.disconnect(this._focusSignal);
        }
        // Remove panel indicator
        if (this._trayButton) {
            this._trayButton.destroy();
            this._trayButton = null;
        }
    }

    _setupDBusService() {
        const VoxVibeInterface = `
        <node>
            <interface name="org.gnome.Shell.Extensions.VoxVibe">
                <method name="GetFocusedWindow">
                    <arg type="s" direction="out" name="windowId"/>
                </method>
                <method name="FocusAndPaste">
                    <arg type="s" direction="in" name="windowId"/>
                    <arg type="s" direction="in" name="text"/>
                    <arg type="b" direction="out" name="success"/>
                </method>
                <method name="GetHistory">
                    <arg type="i" direction="in" name="limit"/>
                    <arg type="s" direction="out" name="historyJson"/>
                </method>
                <method name="ClearHistory">
                    <arg type="b" direction="out" name="success"/>
                </method>
                <signal name="WindowFocused">
                    <arg type="s" name="windowId"/>
                </signal>
            </interface>
        </node>`;

        this._dbusImpl = Gio.DBusExportedObject.wrapJSObject(VoxVibeInterface, this);
        this._dbusImpl.export(Gio.DBus.session, '/org/gnome/Shell/Extensions/VoxVibe');
    }

    _connectSignals() {
        // Track window focus changes
        this._focusSignal = global.display.connect('notify::focus-window', () => {
            const focusedWindow = global.display.focus_window;
            if (focusedWindow) {
                this._lastFocusedWindow = focusedWindow;
                // Emit signal to notify dictation app
                this._dbusImpl.emit_signal('WindowFocused', 
                    GLib.Variant.new('(s)', [this._getWindowId(focusedWindow)]));
            }
        });
    }

    _getWindowId(window) {
        globalThis.log?.(`[VoxVibe] Window ID: ${window.get_pid()}-${window.get_id()}`);
        // Create a unique identifier for the window
        return `${window.get_pid()}-${window.get_id()}`;
    }

    // D-Bus method implementations
    GetFocusedWindow() {
        let result = '';
        if (this._lastFocusedWindow && !this._lastFocusedWindow.destroyed) {
            result = this._getWindowId(this._lastFocusedWindow);
        }
        globalThis.log?.(`[VoxVibe] GetFocusedWindow called, returning: ${result}`);
        return result;
    }

    _setClipboardText(text) {
        globalThis.log?.(`[VoxVibe] _setClipboardText: Setting clipboard and primary to: ${text.slice(0, 40)}...`);
        const clipboard = St.Clipboard.get_default();
        clipboard.set_text(St.ClipboardType.CLIPBOARD, text);
        clipboard.set_text(St.ClipboardType.PRIMARY, text);
    }

    _triggerPasteHack() {
        globalThis.log?.(`[VoxVibe] _triggerPasteHack: Will simulate Ctrl+V after delay`);
        // Use a 100ms delay to ensure clipboard is set
        GLib.timeout_add(GLib.PRIORITY_DEFAULT, 100, () => {
            try {
                const seat = Clutter.get_default_backend().get_default_seat();
                const virtualDevice = seat.create_virtual_device(Clutter.InputDeviceType.KEYBOARD_DEVICE);
                // Press Ctrl
                virtualDevice.notify_keyval(global.get_current_time(), Clutter.KEY_Control_L, Clutter.KeyState.PRESSED);
                // Press V
                virtualDevice.notify_keyval(global.get_current_time(), Clutter.KEY_v, Clutter.KeyState.PRESSED);
                // Release V
                virtualDevice.notify_keyval(global.get_current_time(), Clutter.KEY_v, Clutter.KeyState.RELEASED);
                // Release Ctrl
                virtualDevice.notify_keyval(global.get_current_time(), Clutter.KEY_Control_L, Clutter.KeyState.RELEASED);
                globalThis.log?.(`[VoxVibe] _triggerPasteHack: Ctrl+V simulated successfully`);
            } catch (pasteErr) {
                globalThis.log?.(`[VoxVibe] ERROR during _triggerPasteHack: ${pasteErr}`);
            }
            // Return false to remove the timeout (run only once)
            return false;
        });
    }

    FocusAndPaste(windowId, text) {
        globalThis.log?.(`[VoxVibe] FocusAndPaste called with windowId: ${windowId}, text: ${text.slice(0, 40)}...`);
        try {
            // 1. Find and focus the window
            globalThis.log?.(`[VoxVibe] Step 1: Searching for window with ID ${windowId}`);
            const windows = global.get_window_actors();
            let found = false;
            for (let windowActor of windows) {
                const window = windowActor.get_meta_window();
                if (this._getWindowId(window) === windowId) {
                    globalThis.log?.(`[VoxVibe] Step 1: Focusing window ${windowId}`);
                    window.activate(global.get_current_time());
                    found = true;
                    break;
                }
            }
            if (!found) {
                globalThis.log?.(`[VoxVibe] FocusAndPaste: window not found for ID ${windowId}`);
                return false;
            }
            // 2. Set clipboard content (both CLIPBOARD and PRIMARY)
            this._setClipboardText(text);
            // 3. Trigger paste after a short delay
            this._triggerPasteHack();
            return true;
        } catch (e) {
            globalThis.log?.(`[VoxVibe] Error in FocusAndPaste: ${e}`);
            console.error('Error in FocusAndPaste:', e);
            return false;
        }
    }

    GetHistory(limit) {
        globalThis.log?.(`[VoxVibe] GetHistory called with limit: ${limit}`);
        try {
            // Spawn Python script to read history
            const python_cmd = ['python3', '-c', `
import sys
import os
import json
from pathlib import Path

# Try to find the voxvibe package
possible_paths = [
    os.path.join(os.path.expanduser('~'), 'code', 'voice-flow', 'app'),
    os.path.join(os.path.expanduser('~'), 'code', 'voxvibe', 'app'),
    '/opt/voxvibe/app',
    os.path.join(os.getcwd(), 'app')
]

voxvibe_path = None
for path in possible_paths:
    if os.path.exists(os.path.join(path, 'voxvibe', 'history_storage.py')):
        voxvibe_path = path
        break

if voxvibe_path:
    sys.path.insert(0, voxvibe_path)
    from voxvibe.history_storage import HistoryStorage
    storage = HistoryStorage()
    history = storage.get_history(${limit} if ${limit} > 0 else None)
    result = []
    for entry_id, text, timestamp in history:
        result.append({'id': entry_id, 'text': text, 'timestamp': timestamp.isoformat()})
    print(json.dumps(result))
else:
    print('[]')
`];
            
            const [success, stdout, stderr] = GLib.spawn_sync(
                null, python_cmd, null, 
                GLib.SpawnFlags.SEARCH_PATH, null
            );
            
            if (success && stdout) {
                const output = new TextDecoder().decode(stdout).trim();
                globalThis.log?.(`[VoxVibe] GetHistory result: ${output.slice(0, 100)}...`);
                return output;
            } else {
                globalThis.log?.(`[VoxVibe] GetHistory failed: ${stderr ? new TextDecoder().decode(stderr) : 'unknown error'}`);
                return '[]';
            }
        } catch (e) {
            globalThis.log?.(`[VoxVibe] Error in GetHistory: ${e}`);
            return '[]';
        }
    }

    ClearHistory() {
        globalThis.log?.(`[VoxVibe] ClearHistory called`);
        try {
            // Spawn Python script to clear history
            const python_cmd = ['python3', '-c', `
import sys
import os

# Try to find the voxvibe package
possible_paths = [
    os.path.join(os.path.expanduser('~'), 'code', 'voice-flow', 'app'),
    os.path.join(os.path.expanduser('~'), 'code', 'voxvibe', 'app'),
    '/opt/voxvibe/app',
    os.path.join(os.getcwd(), 'app')
]

voxvibe_path = None
for path in possible_paths:
    if os.path.exists(os.path.join(path, 'voxvibe', 'history_storage.py')):
        voxvibe_path = path
        break

if voxvibe_path:
    sys.path.insert(0, voxvibe_path)
    from voxvibe.history_storage import HistoryStorage
    storage = HistoryStorage()
    success = storage.clear_history()
    print('true' if success else 'false')
else:
    print('false')
`];
            
            const [success, stdout, stderr] = GLib.spawn_sync(
                null, python_cmd, null, 
                GLib.SpawnFlags.SEARCH_PATH, null
            );
            
            if (success) {
                const output = new TextDecoder().decode(stdout).trim();
                const result = output === 'true';
                globalThis.log?.(`[VoxVibe] ClearHistory result: ${result}`);
                return result;
            } else {
                globalThis.log?.(`[VoxVibe] ClearHistory failed: ${stderr ? new TextDecoder().decode(stderr) : 'unknown error'}`);
                return false;
            }
        } catch (e) {
            globalThis.log?.(`[VoxVibe] Error in ClearHistory: ${e}`);
            return false;
        }
    }

    _showHistoryPopover() {
        globalThis.log?.(`[VoxVibe] _showHistoryPopover called`);
        try {
            // Get history data
            const historyJson = this.GetHistory(30);
            const history = JSON.parse(historyJson);
            
            if (history.length === 0) {
                Main.notify('VoxVibe', 'No transcription history found');
                return;
            }
            
            // Create a simple dialog to show history
            const dialog = new St.BoxLayout({
                vertical: true,
                style_class: 'modal-dialog',
                style: 'background-color: rgba(0,0,0,0.8); padding: 20px; border-radius: 10px; max-width: 400px;'
            });
            
            // Add title
            const title = new St.Label({
                text: 'Transcription History',
                style: 'font-size: 16px; font-weight: bold; color: white; margin-bottom: 10px;'
            });
            dialog.add_child(title);
            
            // Add history items (show only first 10)
            const itemsToShow = history.slice(0, 10);
            for (let i = 0; i < itemsToShow.length; i++) {
                const item = itemsToShow[i];
                const itemText = item.text.length > 50 ? item.text.slice(0, 50) + '...' : item.text;
                
                const itemButton = new St.Button({
                    label: `${i + 1}. ${itemText}`,
                    style: 'background-color: rgba(255,255,255,0.1); color: white; padding: 8px; margin: 2px; border-radius: 5px; text-align: left;',
                    x_expand: true
                });
                
                itemButton.connect('clicked', () => {
                    this._setClipboardText(item.text);
                    Main.notify('VoxVibe', 'Text copied to clipboard');
                    Main.layoutManager.removeChrome(modalContainer);
                });
                
                dialog.add_child(itemButton);
            }
            
            // Add close button
            const closeButton = new St.Button({
                label: 'Close',
                style: 'background-color: rgba(255,0,0,0.7); color: white; padding: 8px; margin-top: 10px; border-radius: 5px;'
            });
            closeButton.connect('clicked', () => {
                Main.layoutManager.removeChrome(modalContainer);
            });
            dialog.add_child(closeButton);
            
            // Create modal container
            const modalContainer = new St.Widget({
                layout_manager: new Clutter.BinLayout(),
                width: global.screen_width,
                height: global.screen_height,
                style: 'background-color: rgba(0,0,0,0.5);'
            });
            
            modalContainer.add_child(dialog);
            dialog.set_position(
                (global.screen_width - 400) / 2,
                (global.screen_height - dialog.height) / 2
            );
            
            Main.layoutManager.addChrome(modalContainer);
            
            // Close on click outside
            modalContainer.connect('button-press-event', (actor, event) => {
                if (event.get_source() === modalContainer) {
                    Main.layoutManager.removeChrome(modalContainer);
                }
                return Clutter.EVENT_PROPAGATE;
            });
            
        } catch (e) {
            globalThis.log?.(`[VoxVibe] Error in _showHistoryPopover: ${e}`);
            Main.notify('VoxVibe', 'Error showing history');
        }
    }
}
