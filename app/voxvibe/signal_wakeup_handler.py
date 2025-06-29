"""Qt signal wakeup handler.

This helper class bridges POSIX signal handling with the Qt event loop by
leveraging Python's ``signal.set_wakeup_fd`` mechanism.  A dedicated
``socketpair`` is created; the write-end is registered with the Python
signal machinery while the read-end is handed to a ``QAbstractSocket``
instance so that Qt will wake up and emit a ``readyRead`` signal whenever a
POSIX signal is delivered.  This allows your application to handle signals
(e.g. SIGINT, SIGTERM) in the Qt thread without resorting to polling.
"""

from __future__ import annotations

import logging
import signal
import socket
from typing import Optional

from PyQt6.QtNetwork import QAbstractSocket

logger = logging.getLogger(__name__)


class SignalWakeupHandler(QAbstractSocket):
    """Propagates system signals from Python to the Qt event loop."""

    def __init__(self, parent: Optional[object] = None):
        # We purposely choose a UDP socket (datagram) so that we can transfer a
        # single byte per signal without the overhead of a stream protocol.
        super().__init__(QAbstractSocket.SocketType.UdpSocket, parent)

        # Create a pair of connected sockets; one end will be written to by the
        # Python signal handler, the other end is watched by Qt.
        self._writer, self._reader = socket.socketpair(type=socket.SOCK_DGRAM)
        self._writer.setblocking(False)

        # Tell Python to write a byte to the writer's fd whenever a signal is
        # delivered.  Store the previous fd so we can restore it on cleanup.
        self._old_fd = signal.set_wakeup_fd(self._writer.fileno())

        # Give Qt ownership of the reader fd so that ``readyRead`` is emitted
        # in the main thread.
        self.setSocketDescriptor(self._reader.fileno())

        # Whenever Qt notifies us that data is available, consume and discard
        # it.  We don't need the actual signal number here – we only need Qt to
        # wake up so that the Python layer can run its registered handler.
        self.readyRead.connect(self._consume_signal)

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _consume_signal(self) -> None:
        """Read and discard the pending byte to clear the socket buffer."""
        try:
            self.readData(1)
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug("SignalWakeupHandler consume error: %s", exc)

    # ------------------------------------------------------------------
    # Qt object lifecycle
    # ------------------------------------------------------------------
    def __del__(self) -> None:  # noqa: D401 – simple verb tense is fine here
        """Restore the original wake-up fd when the object is garbage-collected."""
        if hasattr(self, "_old_fd") and self._old_fd is not None:
            try:
                signal.set_wakeup_fd(self._old_fd)
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug("Failed to restore previous wakeup fd: %s", exc)
