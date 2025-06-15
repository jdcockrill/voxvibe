// extension.js - GNOME Extension for Dictation App Window Management
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

export default class DictationWindowExtension extends Extension {
    enable() {
        this._lastFocusedWindow = null;
        this._dbusImpl = null;
        this._setupDBusService();
        this._connectSignals();
    }

    disable() {
        if (this._dbusImpl) {
            this._dbusImpl.unexport();
            this._dbusImpl = null;
        }
        if (this._focusSignal) {
            global.display.disconnect(this._focusSignal);
        }
    }

    _setupDBusService() {
        const DictationInterface = `
        <node>
            <interface name="org.gnome.Shell.Extensions.Dictation">
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

        this._dbusImpl = Gio.DBusExportedObject.wrapJSObject(DictationInterface, this);
        this._dbusImpl.export(Gio.DBus.session, '/org/gnome/Shell/Extensions/Dictation');
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
        // Create a unique identifier for the window
        return `${window.get_pid()}-${window.get_id()}`;
    }

    // D-Bus method implementations
    GetFocusedWindow() {
        if (this._lastFocusedWindow && !this._lastFocusedWindow.is_destroyed()) {
            return this._getWindowId(this._lastFocusedWindow);
        }
        return '';
    }

    FocusAndPaste(windowId, text) {
        try {
            // 1. Find and focus the window
            const windows = global.get_window_actors();
            let found = false;
            for (let windowActor of windows) {
                const window = windowActor.get_meta_window();
                if (this._getWindowId(window) === windowId) {
                    window.focus(global.get_current_time());
                    found = true;
                    break;
                }
            }
            if (!found) {
                return false;
            }
            // 2. Set clipboard content
            const St = imports.gi.St;
            const Clutter = imports.gi.Clutter;
            const clipboard = St.Clipboard.get_default();
            clipboard.set_text(St.ClipboardType.CLIPBOARD, text);

            // 3. Simulate Ctrl+V
            const seat = Clutter.get_default_backend().get_default_seat();
            const virtualDevice = seat.create_virtual_device(Clutter.InputDeviceType.KEYBOARD_DEVICE);
            // Press Ctrl
            virtualDevice.notify_key(global.get_current_time(), Clutter.KEY_Control_L, Clutter.KeyState.PRESSED);
            // Press V
            virtualDevice.notify_key(global.get_current_time(), Clutter.KEY_v, Clutter.KeyState.PRESSED);
            // Release V
            virtualDevice.notify_key(global.get_current_time(), Clutter.KEY_v, Clutter.KeyState.RELEASED);
            // Release Ctrl
            virtualDevice.notify_key(global.get_current_time(), Clutter.KEY_Control_L, Clutter.KeyState.RELEASED);
            return true;
        } catch (e) {
            console.error('Error in FocusAndPaste:', e);
            return false;
        }
    }
}
