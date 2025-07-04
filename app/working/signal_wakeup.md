The Qt event loop is implemented in C(++). That means, that while it runs and no Python code is called (eg. by a Qt signal connected to a Python slot), the signals are noted, but the Python signal handlers aren't called.

But, since Python 2.6 and in Python 3 you can cause Qt to run a Python function when a signal with a handler is received using signal.set_wakeup_fd().

This is possible, because, contrary to the documentation, the low-level signal handler doesn't only set a flag for the virtual machine, but it may also write a byte into the file descriptor set by set_wakeup_fd(). Python 2 writes a NUL byte, Python 3 writes the signal number.

So by subclassing a Qt class that takes a file descriptor and provides a readReady() signal, like e.g. QAbstractSocket, the event loop will execute a Python function every time a signal (with a handler) is received causing the signal handler to execute nearly instantaneous without need for timers:

```python
import sys, signal, socket
from PyQt4 import QtCore, QtNetwork

class SignalWakeupHandler(QtNetwork.QAbstractSocket):

    def __init__(self, parent=None):
        super().__init__(QtNetwork.QAbstractSocket.UdpSocket, parent)
        self.old_fd = None
        # Create a socket pair
        self.wsock, self.rsock = socket.socketpair(type=socket.SOCK_DGRAM)
        # Let Qt listen on the one end
        self.setSocketDescriptor(self.rsock.fileno())
        # And let Python write on the other end
        self.wsock.setblocking(False)
        self.old_fd = signal.set_wakeup_fd(self.wsock.fileno())
        # First Python code executed gets any exception from
        # the signal handler, so add a dummy handler first
        self.readyRead.connect(lambda : None)
        # Second handler does the real handling
        self.readyRead.connect(self._readSignal)

    def __del__(self):
        # Restore any old handler on deletion
        if self.old_fd is not None and signal and signal.set_wakeup_fd:
            signal.set_wakeup_fd(self.old_fd)

    def _readSignal(self):
        # Read the written byte.
        # Note: readyRead is blocked from occuring again until readData()
        # was called, so call it, even if you don't need the value.
        data = self.readData(1)
        # Emit a Qt signal for convenience
        self.signalReceived.emit(data[0])

    signalReceived = QtCore.pyqtSignal(int)

app = QApplication(sys.argv)
SignalWakeupHandler(app)

signal.signal(signal.SIGINT, lambda sig,_: app.quit())

sys.exit(app.exec_())
```
