The asynchronous approach by cg909 / Michael Herrmann is quite interesting to replace timers. Thus, here is a simplified version which also uses the default type for socket.socketpair (SOCK_STREAM).

```python
class SignalWatchdog(QtNetwork.QAbstractSocket):
def __init__(self):
    """ Propagates system signals from Python to QEventLoop """
    super().__init__(QtNetwork.QAbstractSocket.SctpSocket, None)
    self.writer, self.reader = socket.socketpair()
    self.writer.setblocking(False)
    signal.set_wakeup_fd(self.writer.fileno())  # Python hook
    self.setSocketDescriptor(self.reader.fileno())  # Qt hook
    self.readyRead.connect(lambda: None)  # Dummy function call
```

This, together with cg909's post, is the correct answer.
