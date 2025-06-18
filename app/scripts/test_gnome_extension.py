import time

from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage

BUS_NAME = "org.gnome.Shell"
OBJECT_PATH = "/org/gnome/Shell/Extensions/VoxVibe"
INTERFACE = "org.gnome.Shell.Extensions.VoxVibe"

def main():
    bus = QDBusConnection.sessionBus()
    iface = QDBusInterface(BUS_NAME, OBJECT_PATH, INTERFACE, bus)
    if not iface.isValid():
        print("DBus interface not available. Is the GNOME extension running?")
        return

    # Test GetFocusedWindow
    reply = iface.call("GetFocusedWindow")
    if reply.type() == QDBusMessage.MessageType.ErrorMessage:
        print("GetFocusedWindow failed:", reply.errorMessage())
        return
    print("GetFocusedWindow reply:", reply.arguments())

    window_id = reply.arguments()[0] if reply.arguments() else ""
    print("Focused window ID:", window_id)
    if not window_id:
        print("No window is currently focused.")
        return

    # sleep 2s
    time.sleep(2)

    # Test FocusAndPaste
    test_text = "Hello, World!"
    reply = iface.call("FocusAndPaste", window_id, test_text)
    if reply.type() == QDBusMessage.MessageType.ErrorMessage:
        print("FocusAndPaste failed:", reply.errorMessage())
        return

    success = bool(reply.arguments()[0]) if reply.arguments() else False
    print("FocusAndPaste success:", success)

if __name__ == "__main__":
    main()