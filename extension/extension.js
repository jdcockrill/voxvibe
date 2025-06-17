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
        this._trayButton = new PanelMenu.Button(0.0, 'Voice-Flow Indicator', false);
        const icon = new St.Icon({
            icon_name: 'audio-input-microphone-symbolic',
            style_class: 'system-status-icon',
        });
        this._trayButton.add_child(icon);
        // Add menu item showing app name and version (non-interactive)
        const appInfoItem = new PopupMenu.PopupMenuItem('VoxVibe v1');
        appInfoItem.setSensitive(false);
        this._trayButton.menu.addMenuItem(appInfoItem);
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
}
