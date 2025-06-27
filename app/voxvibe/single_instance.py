"""Single-instance guard using QLocalServer.

Usage::

    from .single_instance import SingleInstance, SingleInstanceError

    with SingleInstance("voxvibe_single_instance"):
        ...  # your application code

Pass ``reset=True`` to force removal of any stale socket before trying to
acquire the lock.
"""

import logging
from contextlib import AbstractContextManager
from typing import Optional

from PyQt6.QtNetwork import QLocalServer, QLocalSocket

logger = logging.getLogger(__name__)

__all__ = ["SingleInstance", "SingleInstanceError"]


class SingleInstanceError(RuntimeError):
    """Raised when another instance is already running."""


class SingleInstance(AbstractContextManager):
    """Context manager ensuring a single running instance via QLocalServer.

    When entering, it tries to listen on a QLocalServer with the specified key.
    If another instance is detected it raises :class:`SingleInstanceError`.

    ``reset`` forces any pre-existing stale socket to be removed first.
    """

    def __init__(self, key: str, *, reset: bool = False):
        self._key = key
        self._reset = reset
        self._server: Optional[QLocalServer] = None

    # ------------------------------------------------------------------
    # Context manager API
    # ------------------------------------------------------------------
    def __enter__(self):
        # Optionally remove stale socket before attempting to listen
        if self._reset:
            logger.info("Reset flag provided – removing any existing server entry")
            QLocalServer.removeServer(self._key)

        self._server = QLocalServer()

        # Attempt to listen; if it fails we check if it is because the address
        # is in use by a *running* process or a stale socket path.
        if not self._server.listen(self._key):
            # Attempt to connect. If connection succeeds, another instance is
            # live; otherwise it's likely a stale socket.
            logger.debug("Listen failed – attempting to connect to determine stale vs running instance")
            socket = QLocalSocket()
            socket.connectToServer(self._key)
            if socket.waitForConnected(100):  # ms
                socket.close()
                raise SingleInstanceError("Another instance is already running.")
            else:
                # Stale socket – remove and retry once
                logger.warning("Stale local socket detected; removing and retrying once")
                QLocalServer.removeServer(self._key)
                if not self._server.listen(self._key):
                    # Give up – cannot obtain lock
                    raise SingleInstanceError("Another instance may be starting up. Please try again in a moment.")

        logger.info("Single-instance lock acquired via QLocalServer")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._server and self._server.isListening():
            self._server.close()
            QLocalServer.removeServer(self._key)
            logger.info("Single-instance lock released and socket removed")
        # Propagate exceptions, if any
        return False
