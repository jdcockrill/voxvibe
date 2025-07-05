// extension.js - GNOME Extension for Dictation App Window Management
import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

import Clutter from 'gi://Clutter';
import St from 'gi://St';

import Meta from 'gi://Meta';
import Shell from 'gi://Shell';

// High-level DBus proxy for the Python VoxVibe service
const VoxVibeServiceProxy = Gio.DBusProxy.makeProxyWrapper(`
    <node>
        <interface name="app.voxvibe.Service">
            <method name="TriggerHotkey"/>
        </interface>
    </node>`);

import * as Main from 'resource:///org/gnome/shell/ui/main.js';

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
        globalThis.log?.('[VoxVibe] enabling extension');
        this._setupDBusService();
        globalThis.log?.('[VoxVibe] DBus service setup');
        this._connectSignals();
        globalThis.log?.('[VoxVibe] signals connected');
        this._settings = this._settings || this.getSettings();
        globalThis.log?.('[VoxVibe] settings loaded');
        globalThis.log?.('[VoxVibe] importing GNOME modules');
        const action = Main.wm.addKeybinding(
            'launch-hotkey',
            this._settings,
            Meta.KeyBindingFlags.IGNORE_AUTOREPEAT,
            Shell.ActionMode.ALL,
            this._onHotkey.bind(this)
        );
        if (action === imports.gi.Meta.KeyBindingAction.NONE) {
            globalThis.log?.('[VoxVibe] Failed to register hotkey – action NONE');
        } else {
            globalThis.log?.('[VoxVibe] Hotkey registered, action: ' + action);
        }
    }

    disable() {
        Main.wm.removeKeybinding('launch-hotkey');
        if (this._dbusImpl) {
            this._dbusImpl.unexport();
            this._dbusImpl = null;
        }
        if (this._focusSignal) {
            global.display.disconnect(this._focusSignal);
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

    _onHotkey() {
        globalThis.log?.('[VoxVibe] Super+X hotkey activated!');
        this._triggerPythonHotkey();
    }

    _triggerPythonHotkey() {
        try {
            if (!this._voxProxy) {
                this._voxProxy = new VoxVibeServiceProxy(
                    Gio.DBus.session,
                    'app.voxvibe.Service', // Service name from Python
                    '/app/voxvibe/Service' // Object path
                );
            }
            // Use the asynchronous D-Bus method to avoid blocking the GNOME Shell
            // JS thread. The Remote variant returns immediately and delivers the
            // call in the background, preventing UI hangs.
            this._voxProxy.TriggerHotkeyRemote((result, error) => {
                if (error) {
                    globalThis.log?.(`[VoxVibe] TriggerHotkeyRemote error: ${error}`);
                }
            });
            globalThis.log?.('[VoxVibe] TriggerHotkey DBus call sent');
        } catch (err) {
            globalThis.log?.(`[VoxVibe] Failed to call TriggerHotkey: ${err}`);
        }
    }

    _connectSignals() {
        // Track window focus changes
        this._focusSignal = global.display.connect('notify::focus-window', () => {
            const focusedWindow = global.display.focus_window;
            if (focusedWindow) {
                this._lastFocusedWindow = focusedWindow;
                // Emit signal to notify dictation app
                this._dbusImpl.emit_signal('WindowFocused', 
                    GLib.Variant.new('(s)', [this._getWindowInfo(focusedWindow)]));
            }
        });
    }

    _getWindowInfo(window) {
        const windowInfo = {
            title: window.get_title() || "",
            wm_class: window.get_wm_class() || "",
            id: window.get_id()
        };
        globalThis.log?.(`[VoxVibe] Window Info: ${JSON.stringify(windowInfo)}`);
        return JSON.stringify(windowInfo);
    }

    // D-Bus method implementations
    GetFocusedWindow() {
        let result = '';
        if (this._lastFocusedWindow && !this._lastFocusedWindow.destroyed) {
            result = this._getWindowInfo(this._lastFocusedWindow);
        }
        globalThis.log?.(`[VoxVibe] GetFocusedWindow called, returning: ${result}`);
        return result;
    }

    _backupClipboard() {
        globalThis.log?.(`[VoxVibe] _backupClipboard: Backing up clipboard content`);
        const clipboard = St.Clipboard.get_default();
        
        // Store backup object to restore later
        this._clipboardBackup = {
            clipboard: null,
            primary: null
        };
        
        // Get current clipboard content (this is async, but we'll handle it synchronously for now)
        try {
            clipboard.get_content(St.ClipboardType.CLIPBOARD, (clipboard, content) => {
                if (content) {
                    this._clipboardBackup.clipboard = content;
                    globalThis.log?.(`[VoxVibe] _backupClipboard: Clipboard content backed up`);
                } else {
                    globalThis.log?.(`[VoxVibe] _backupClipboard: No clipboard content to backup`);
                }
            });
            
            clipboard.get_content(St.ClipboardType.PRIMARY, (clipboard, content) => {
                if (content) {
                    this._clipboardBackup.primary = content;
                    globalThis.log?.(`[VoxVibe] _backupClipboard: Primary content backed up`);
                } else {
                    globalThis.log?.(`[VoxVibe] _backupClipboard: No primary content to backup`);
                }
            });
        } catch (error) {
            globalThis.log?.(`[VoxVibe] _backupClipboard: Error backing up clipboard: ${error}`);
        }
    }

    _restoreClipboard() {
        globalThis.log?.(`[VoxVibe] _restoreClipboard: Restoring clipboard content`);
        
        if (!this._clipboardBackup) {
            globalThis.log?.(`[VoxVibe] _restoreClipboard: No backup to restore`);
            return;
        }
        
        const clipboard = St.Clipboard.get_default();
        
        try {
            // Restore clipboard content
            if (this._clipboardBackup.clipboard) {
                clipboard.set_content(St.ClipboardType.CLIPBOARD, this._clipboardBackup.clipboard);
                globalThis.log?.(`[VoxVibe] _restoreClipboard: Clipboard content restored`);
            }
            
            // Restore primary content
            if (this._clipboardBackup.primary) {
                clipboard.set_content(St.ClipboardType.PRIMARY, this._clipboardBackup.primary);
                globalThis.log?.(`[VoxVibe] _restoreClipboard: Primary content restored`);
            }
            
            // Clear backup
            this._clipboardBackup = null;
            globalThis.log?.(`[VoxVibe] _restoreClipboard: Backup cleared`);
        } catch (error) {
            globalThis.log?.(`[VoxVibe] _restoreClipboard: Error restoring clipboard: ${error}`);
        }
    }

    _setClipboardText(text) {
        globalThis.log?.(`[VoxVibe] _setClipboardText: Setting clipboard and primary to: ${text.slice(0, 40)}...`);
        const clipboard = St.Clipboard.get_default();
        clipboard.set_text(St.ClipboardType.CLIPBOARD, text);
        clipboard.set_text(St.ClipboardType.PRIMARY, text);
    }

    _triggerPasteHack() {
        globalThis.log?.(`[VoxVibe] _triggerPasteHack: Will simulate Ctrl+Shift+V after delay`);
        // Use a 100ms delay to ensure clipboard is set
        GLib.timeout_add(GLib.PRIORITY_DEFAULT, 100, () => {
            try {
                const seat = Clutter.get_default_backend().get_default_seat();
                const virtualDevice = seat.create_virtual_device(Clutter.InputDeviceType.KEYBOARD_DEVICE);
                // Press Ctrl
                virtualDevice.notify_keyval(global.get_current_time(), Clutter.KEY_Control_L, Clutter.KeyState.PRESSED);
                // Press Shift
                virtualDevice.notify_keyval(global.get_current_time(), Clutter.KEY_Shift_L, Clutter.KeyState.PRESSED);
                // Press V
                virtualDevice.notify_keyval(global.get_current_time(), Clutter.KEY_v, Clutter.KeyState.PRESSED);
                // Release V
                virtualDevice.notify_keyval(global.get_current_time(), Clutter.KEY_v, Clutter.KeyState.RELEASED);
                // Release Shift
                virtualDevice.notify_keyval(global.get_current_time(), Clutter.KEY_Shift_L, Clutter.KeyState.RELEASED);
                // Release Ctrl
                virtualDevice.notify_keyval(global.get_current_time(), Clutter.KEY_Control_L, Clutter.KeyState.RELEASED);
                globalThis.log?.(`[VoxVibe] _triggerPasteHack: Ctrl+Shift+V simulated successfully`);
                
                // Restore clipboard after paste operation completes
                // Use a 200ms delay to ensure paste operation is complete
                GLib.timeout_add(GLib.PRIORITY_DEFAULT, 200, () => {
                    this._restoreClipboard();
                    return false; // Remove timeout
                });
            } catch (pasteErr) {
                globalThis.log?.(`[VoxVibe] ERROR during _triggerPasteHack: ${pasteErr}`);
                // Still try to restore clipboard even if paste failed
                GLib.timeout_add(GLib.PRIORITY_DEFAULT, 200, () => {
                    this._restoreClipboard();
                    return false; // Remove timeout
                });
            }
            // Return false to remove the timeout (run only once)
            return false;
        });
    }

    FocusAndPaste(windowId, text) {
        globalThis.log?.(`[VoxVibe] FocusAndPaste called with windowId: ${windowId}, text: ${text.slice(0, 40)}...`);
        try {
            // Convert string windowId to integer for comparison
            const windowIdInt = parseInt(windowId);
            if (isNaN(windowIdInt)) {
                globalThis.log?.(`[VoxVibe] Invalid windowId: ${windowId}`);
                return false;
            }
            
            // 1. Find and focus the window
            globalThis.log?.(`[VoxVibe] Step 1: Searching for window with ID ${windowIdInt}`);
            const windows = global.get_window_actors();
            let found = false;
            for (let windowActor of windows) {
                const window = windowActor.get_meta_window();
                if (window.get_id() === windowIdInt) {
                    globalThis.log?.(`[VoxVibe] Step 1: Focusing window ${windowIdInt}`);
                    window.activate(global.get_current_time());
                    found = true;
                    break;
                }
            }
            if (!found) {
                globalThis.log?.(`[VoxVibe] FocusAndPaste: window not found for ID ${windowIdInt}`);
                return false;
            }
            
            // 2. Backup current clipboard content before replacing
            this._backupClipboard();
            
            // 3. Set clipboard content (both CLIPBOARD and PRIMARY)
            this._setClipboardText(text);
            
            // 4. Trigger paste after a short delay (restore happens in _triggerPasteHack)
            this._triggerPasteHack();
            return true;
        } catch (e) {
            globalThis.log?.(`[VoxVibe] Error in FocusAndPaste: ${e}`);
            console.error('Error in FocusAndPaste:', e);
            // Try to restore clipboard even if there was an error
            if (this._clipboardBackup) {
                this._restoreClipboard();
            }
            return false;
        }
    }
}
