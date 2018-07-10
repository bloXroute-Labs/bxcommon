import errno
import socket
import time

from bxcommon.connections.connection_state import ConnectionState
from bxcommon.constants import MAX_BAD_MESSAGES, RECV_BUFSIZE, HDR_COMMON_OFF
from bxcommon.exceptions import UnrecognizedCommandError, PayloadLenError
from bxcommon.messages import Message, AckMessage, PongMessage
from bxcommon.utils import OutputBuffer, InputBuffer, log_debug, log_err


class AbstractConnection(object):
    def __init__(self, sock, address, node, from_me=False, setup=False):
        self.sock = sock
        self.fileno = sock.fileno()

        # (IP, Port) at time of socket creation. We may get a new application level port in
        # the version message if the connection is not from me.
        self.peer_ip, self.peer_port = address
        self.my_ip = node.server_ip
        self.my_port = node.server_port

        self.from_me = from_me  # Whether or not I initiated the connection
        self.setup = setup  # Whether or not I set up this connection

        self.outputbuf = OutputBuffer()
        self.inputbuf = InputBuffer()
        self.node = node

        self.is_persistent = False
        self.sendable = False  # Whether or not I can send more bytes on this socket.
        self.state = ConnectionState.CONNECTING

        # Temporary buffers to receive the contents of the recv call.
        self.recv_buf = bytearray(RECV_BUFSIZE)

        # Number of bad messages I've received in a row.
        self.num_bad_messages = 0

        self.peer_desc = "%s %d" % (self.peer_ip, self.peer_port)
        
        self.message_handlers = None

    # Marks a connection as 'sendable', that is, there is room in the outgoing send buffer, and a send call can succeed.
    # Only gets unmarked when the outgoing send buffer is full.
    def mark_sendable(self):
        self.sendable = True

    def can_send_queued(self):
        return self.sendable

    def pre_process_msg(self, msg_cls):
        is_full_msg, msg_type, payload_len = msg_cls.peek_message(self.inputbuf)

        log_debug("XXX: Starting to get message of type {0}. Is full: {1}".format(msg_type, is_full_msg))

        return is_full_msg, msg_type, payload_len

        # Enqueues the contents of a Message instance, msg, to our outputbuf and attempts to send it if the underlying
        #   socket has room in the send buffer.

    def enqueue_msg(self, msg):
        if self.state & ConnectionState.MARK_FOR_CLOSE:
            return

        self.outputbuf.enqueue_msgbytes(msg.rawbytes())

        if self.can_send_queued():
            self.send()

        # Enqueues the raw bytes of a message, msg_bytes, to our outputbuf and attempts to send it if the
        #   underlying socket has room in the send buffer.

    def enqueue_msg_bytes(self, msg_bytes):
        if self.state & ConnectionState.MARK_FOR_CLOSE:
            return

        size = len(msg_bytes)

        log_debug("Adding message of length {0} to {1}'s outputbuf".format(size, self.peer_desc))

        self.outputbuf.enqueue_msgbytes(msg_bytes)

        if self.can_send_queued():
            self.send()

    def send(self):
        raise NotImplementedError()

    # Receives and processes the next bytes on the socket's inputbuffer.
    # Returns 0 in order to avoid being rescheduled if this was an alarm.
    def recv(self, msg_cls=Message, hello_msgs=['hello', 'ack']):
        self.collect_input()

        while True:
            if self.state & ConnectionState.MARK_FOR_CLOSE:
                return 0

            is_full_msg, msg_type, payload_len = self.pre_process_msg(msg_cls)

            if not is_full_msg:
                break

            # Full messages must be a version or verack if the connection isn't established yet.
            msg = self.pop_next_message(payload_len)
            # If there was some error in parsing this message, then continue the loop.
            if msg is None:
                if self.num_bad_messages == MAX_BAD_MESSAGES:
                    log_debug("Got enough bad messages! Marking connection from {0} closed".format(self.peer_desc))
                    self.state |= ConnectionState.MARK_FOR_CLOSE
                    return 0  # I have MAX_BAD_MESSAGES messages that failed to parse in a row.

                self.num_bad_messages += 1
                continue

            self.num_bad_messages = 0

            if not (self.state & ConnectionState.ESTABLISHED) and msg_type not in hello_msgs:
                log_err("Connection to {0} not established and got {1} message!  Closing."
                        .format(self.peer_desc, msg_type))
                self.state |= ConnectionState.MARK_FOR_CLOSE
                return 0

            log_debug("Received message of type {0} from {1}".format(msg_type, self.peer_desc))

            if msg_type in self.message_handlers:
                msg_handler = self.message_handlers[msg_type]
                msg_handler(msg)

        log_debug("Done receiving from {0}".format(self.peer_desc))
        return 0

    # Pop the next message off of the buffer given the message length.
    # Preserve invariant of self.inputbuf always containing the start of a valid message.
    def pop_next_message(self, payload_len, msg_type=Message, hdr_size=HDR_COMMON_OFF):
        try:
            msg_len = hdr_size + payload_len
            msg_contents = self.inputbuf.remove_bytes(msg_len)
            return msg_type.parse(msg_contents)
        except UnrecognizedCommandError as e:
            log_err("Unrecognized command on {0}. Error Message: {1}".format(self.peer_desc, e.msg))
            log_debug("Src: {0} Raw data: {1}".format(self.peer_desc, e.raw_data))
            return None

        except PayloadLenError as e:
            log_err("ParseError on connection {0}.".format(self.peer_desc))
            log_debug("ParseError message: {0}".format(e.msg))
            self.state |= ConnectionState.MARK_FOR_CLOSE  # Close, no retry.
            return None

    # Collect input from the socket and store it in the inputbuffer until either the socket is drained
    # or the throttling limits are hit.
    def collect_input(self):
        log_debug("Collecting input from {0}".format(self.peer_desc))
        collect_input = True

        while collect_input:
            # Read from the socket and store it into the recv buffer.
            try:
                bytes_read = self.sock.recv_into(self.recv_buf, RECV_BUFSIZE)
            except socket.error as e:
                if e.errno in [errno.EAGAIN, errno.EWOULDBLOCK]:
                    log_debug("Received errno {0} with msg {1} on connection {2}. Stop collecting input"
                              .format(e.errno, e.strerror, self.peer_desc))
                    break
                elif e.errno in [errno.EINTR]:
                    # we were interrupted, try again
                    log_debug("Received errno {0} with msg {1}, recv on {2} failed. Continuing recv."
                              .format(e.errno, e.strerror, self.peer_desc))
                    continue
                elif e.errno in [errno.ECONNREFUSED]:
                    # Fatal errors for the connections
                    log_debug("Received errno {0} with msg {1}, recv on {2} failed. Closing connection and retrying..."
                              .format(e.errno, e.strerror, self.peer_desc))
                    self.state |= ConnectionState.MARK_FOR_CLOSE
                    return
                elif e.errno in [errno.ECONNRESET, errno.ETIMEDOUT, errno.EBADF]:
                    # Perform orderly shutdown
                    self.state |= ConnectionState.MARK_FOR_CLOSE
                    return
                elif e.errno in [errno.EFAULT, errno.EINVAL, errno.ENOTCONN, errno.ENOMEM]:
                    # Should never happen errors
                    log_err("Received errno {0} with msg {1}, recv on {2} failed. This should never happen..."
                            .format(e.errno, e.strerror, self.peer_desc))
                    return
                else:
                    raise e

            piece = self.recv_buf[:bytes_read]
            log_debug("Got {0} bytes from {2}. They were: {1}".format(bytes_read, repr(piece), self.peer_desc))

            # A 0 length recv is an orderly shutdown.
            if bytes_read == 0:
                self.state |= ConnectionState.MARK_FOR_CLOSE
                return
            else:
                self.inputbuf.add_bytes(piece)

    # Send bytes to the peer on the given buffer. Return the number of bytes sent.
    # buf must obey the output buffer read interface which has three properties:
    def send_bytes_on_buffer(self, buf, send_one_msg=False):
        total_bytes_written = 0
        byteswritten = 0

        # Send on the socket until either the socket is full or we have nothing else to send.
        while self.sendable and buf.has_more_bytes() > 0 and (not send_one_msg or buf.at_msg_boundary()):
            try:
                byteswritten = self.sock.send(buf.get_buffer())
                total_bytes_written += byteswritten
            except socket.error as e:
                if e.errno in [errno.EAGAIN, errno.EWOULDBLOCK, errno.ENOBUFS]:
                    # Normal operation
                    log_debug("Got {0}. Done sending to {1}. Marking as not sendable."
                              .format(e.strerror, self.peer_desc))
                    self.sendable = False
                elif e.errno in [errno.EINTR]:
                    # Try again later errors
                    log_debug("Got {0}. Send to {1} failed, trying again...".format(e.strerror, self.peer_desc))
                    continue
                elif e.errno in [errno.EACCES, errno.ECONNRESET, errno.EPIPE, errno.EHOSTUNREACH]:
                    # Fatal errors for the connection
                    log_debug("Got {0}, send to {1} failed, closing connection.".format(e.strerror, self.peer_desc))
                    self.state |= ConnectionState.MARK_FOR_CLOSE
                    return 0
                elif e.errno in [errno.ECONNRESET, errno.ETIMEDOUT, errno.EBADF]:
                    # Perform orderly shutdown
                    self.state = ConnectionState.MARK_FOR_CLOSE
                    return 0
                elif e.errno in [errno.EDESTADDRREQ, errno.EFAULT, errno.EINVAL,
                                 errno.EISCONN, errno.EMSGSIZE, errno.ENOTCONN, errno.ENOTSOCK]:
                    # Should never happen errors
                    log_debug("Got {0}, send to {1} failed. Should not have happened..."
                              .format(e.strerror, self.peer_desc))
                    exit(1)
                elif e.errno in [errno.ENOMEM]:
                    # Fatal errors for the node
                    log_debug("Got {0}, send to {1} failed. Fatal error! Shutting down node."
                              .format(e.strerror, self.peer_desc))
                    exit(1)
                else:
                    raise e

            buf.advance_buffer(byteswritten)
            byteswritten = 0

        return total_bytes_written

        # Handle a Hello Message

    def msg_hello(self, msg):
        self.state |= ConnectionState.HELLO_RECVD
        self.enqueue_msg(AckMessage())

        # Handle an Ack Message

    def msg_ack(self, msg):
        self.state |= ConnectionState.HELLO_ACKD

    def msg_ping(self, msg):
        self.enqueue_msg(PongMessage(msg.nonce()))

    def msg_pong(self, msg):
        pass

    # Receive a transaction assignment from txhash -> shortid
    def msg_txassign(self, msg):
        tx_hash = msg.tx_hash()

        log_debug("Processing txassign message")
        if self.node.tx_manager.get_txid(tx_hash) == -1:
            log_debug("Assigning {0} to sid {1}".format(msg.tx_hash(), msg.short_id()))
            self.node.tx_manager.assign_tx_to_sid(tx_hash, msg.short_id(), time.time())
            return tx_hash

        return None

    def close(self):
        log_debug("Closing connection to {0}".format(self.peer_desc))
        self.sock.close()
