import errno
import socket
from typing import TYPE_CHECKING, Callable

from bxcommon import constants
from bxcommon.exceptions import TerminationError
from bxcommon.network.socket_connection_state import SocketConnectionState
from bxcommon.utils import convert
from bxutils import logging
from bxutils.logging.log_level import LogLevel

if TYPE_CHECKING:
    from bxcommon.connections.abstract_node import AbstractNode

logger = logging.get_logger(__name__)


class SocketConnection:
    def __init__(self, socket_instance: socket.socket, node: "AbstractNode",
                 disconnection_scheduler: Callable[[int], None], is_server: bool = False):
        self.socket_instance = socket_instance
        self.is_server = is_server
        self._node = node
        self._disconnect_scheduler = disconnection_scheduler

        self.state = SocketConnectionState.CONNECTING

        self._receive_buf = bytearray(constants.RECV_BUFSIZE)
        self.can_send = False

    def __repr__(self):
        return f"SocketConnection<fileno: {self.fileno()}, server: {self.is_server}>"

    def _log_message(self, level: LogLevel, message, *args, **kwargs):
        logger.log(level, f"[{self}] {message}", *args, **kwargs)

    def log_trace(self, message, *args, **kwargs):
        self._log_message(LogLevel.TRACE, message, *args, **kwargs)

    def log_debug(self, message, *args, **kwargs):
        self._log_message(LogLevel.DEBUG, message, *args, **kwargs)

    def log_info(self, message, *args, **kwargs):
        self._log_message(LogLevel.INFO, message, *args, **kwargs)

    def log_warning(self, message, *args, **kwargs):
        self._log_message(LogLevel.WARNING, message, *args, **kwargs)

    def log_error(self, message, *args, **kwargs):
        self._log_message(LogLevel.ERROR, message, *args, **kwargs)

    def log_fatal(self, message, *args, **kwargs):
        self._log_message(LogLevel.FATAL, message, *args, **kwargs)

    def set_state(self, state: SocketConnectionState):
        self.state |= state

    def mark_for_close(self, should_retry: bool = True):
        self.set_state(SocketConnectionState.MARK_FOR_CLOSE)
        if not should_retry:
            self.set_state(SocketConnectionState.DO_NOT_RETRY)

        self._disconnect_scheduler(self.fileno())

    def is_alive(self) -> bool:
        return not self.state & SocketConnectionState.MARK_FOR_CLOSE

    def receive(self):
        fileno = self.fileno()
        self.log_trace("Collecting input...")

        while self.is_alive():
            # Read from the socket and store it into the receive buffer.
            try:
                bytes_read = self.socket_instance.recv_into(self._receive_buf, constants.RECV_BUFSIZE)
            except socket.error as e:
                if e.errno in [errno.EAGAIN, errno.EWOULDBLOCK]:
                    self.log_trace("Receive completed. Received errno {} with message: {}", e.errno, e.strerror)
                    break
                elif e.errno in [errno.EINTR]:
                    self.log_trace("Receive interrupted: {}. Retrying...", e.strerror)
                    continue
                elif e.errno in [errno.ECONNREFUSED, errno.ECONNRESET, errno.ETIMEDOUT, errno.EBADF]:
                    self.log_info("Receive rejected. Code: {}, message: {}. Closing connection.", e.errno, e.strerror)
                    self.mark_for_close()
                    return
                elif e.errno in [errno.EFAULT, errno.EINVAL, errno.ENOTCONN, errno.ENOMEM]:
                    self.log_error("Receive triggered fatal error. Code: {}, message: {}", e.errno, e.strerror)
                    return
                else:
                    raise e

            piece = self._receive_buf[:bytes_read]
            self.log_trace("Received {} bytes: {}", bytes_read, convert.bytes_to_hex(piece))

            if bytes_read == 0:
                self.log_info("Received orderly close from remote. Closing connection.")
                self.mark_for_close()
                return
            else:
                self._node.on_bytes_received(fileno, piece)

        self._node.on_finished_receiving(fileno)

    def send(self):
        fileno = self.fileno()

        total_bytes_written = 0
        bytes_written = 0

        # Send on the socket until either the socket is full or we have nothing else to send.
        while self.can_send and self.is_alive():
            try:
                send_buffer = self._node.get_bytes_to_send(fileno)
                if not send_buffer:
                    break

                bytes_written = self.socket_instance.send(send_buffer)
                self.log_trace("Sent {} bytes.", bytes_written)
            except socket.error as e:
                if e.errno in [errno.EAGAIN, errno.EWOULDBLOCK, errno.ENOBUFS]:
                    self.log_trace(
                        "Sending filled up socket buffer. Marking as not sendable for now. Message: {}", e.strerror
                    )
                    self.can_send = False
                elif e.errno in [errno.EINTR]:
                    self.log_trace("Sending was interrupted with message: {}. Trying again...", e.strerror)
                    continue
                elif e.errno in [
                    errno.EACCES,
                    errno.ECONNRESET,
                    errno.EPIPE,
                    errno.EHOSTUNREACH,
                    errno.ECONNRESET,
                    errno.ETIMEDOUT,
                    errno.EBADF,
                    errno.ECONNREFUSED,
                ]:
                    self.log_trace("Sending rejected. Code: {}, message: {}", e.errno, e.strerror)
                    self.mark_for_close()
                    return 0

                elif e.errno is errno.ENOTCONN:
                    logger.trace("Got socket error 57 on fileno {}. Marking for close.", fileno)
                    self.mark_for_close()
                    return 0
                elif e.errno in [
                    errno.EDESTADDRREQ,
                    errno.EFAULT,
                    errno.EINVAL,
                    errno.EISCONN,
                    errno.EMSGSIZE,
                    errno.ENOTSOCK,
                ]:
                    # Unrecoverable error. Likely that some developer code has been breaking invariants.
                    self.log_fatal(
                        "Sending triggered fatal socket error. Code: {}, message: {}. Shutting down.",
                        e.errno,
                        e.strerror,
                    )
                    raise TerminationError("Fatal socket error")

                elif e.errno in [errno.ENOMEM]:
                    self.log_fatal(
                        "Sending triggered out of memory. Code: {}, message: {}. Shutting down.", e.errno, e.strerror
                    )
                    raise TerminationError("Socket out of memory")
                else:
                    raise e

            total_bytes_written += bytes_written
            self._node.on_bytes_sent(fileno, bytes_written)

            bytes_written = 0

        return total_bytes_written

    def fileno(self) -> int:
        return self.socket_instance.fileno()

    def dispose(self, force_destroy: bool = False):
        """
        Discard socket resources after socket usage has been disabled.
        SocketConnection is expected to have MARK_FOR_CLOSE state already set on it.

        :param force_destroy: Forcibly dispose of resources even if socket has not been marked for close.
        """
        if not force_destroy and self.is_alive():
            raise ValueError("Attempted to close socket that was not MARK_FOR_CLOSE.")
        try:
            self.socket_instance.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.socket_instance.close()
        self._receive_buf = None
