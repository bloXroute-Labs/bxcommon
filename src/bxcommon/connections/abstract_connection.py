import errno
import socket
import time

from bxcommon.connections.connection_state import ConnectionState
from bxcommon.constants import MAX_BAD_MESSAGES, RECV_BUFSIZE, HDR_COMMON_OFF
from bxcommon.exceptions import UnrecognizedCommandError, PayloadLenError
from bxcommon.messages.ack_message import AckMessage
from bxcommon.messages.message import Message
from bxcommon.messages.pong_message import PongMessage
from bxcommon.utils import logger
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.buffers.output_buffer import OutputBuffer


class AbstractConnection(object):
    def __init__(self, connection_id, address, node, from_me=False, setup=False):
        self.fileno = connection_id

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

        logger.debug("XXX: Starting to get message of type {0}. Is full: {1}".format(msg_type, is_full_msg))

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

        logger.debug("Adding message of length {0} to {1}'s outputbuf".format(size, self.peer_desc))

        self.outputbuf.enqueue_msgbytes(msg_bytes)

        if self.can_send_queued():
            self.send()

    def send(self):
        raise NotImplementedError()

    # Receives and processes the next bytes on the socket's inputbuffer.
    # Returns 0 in order to avoid being rescheduled if this was an alarm.
    def recv(self, msg_cls=Message, hello_msgs=['hello', 'ack']):
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
                    logger.debug("Got enough bad messages! Marking connection from {0} closed".format(self.peer_desc))
                    self.state |= ConnectionState.MARK_FOR_CLOSE
                    return 0  # I have MAX_BAD_MESSAGES messages that failed to parse in a row.

                self.num_bad_messages += 1
                continue

            self.num_bad_messages = 0

            # if not (self.state & ConnectionState.ESTABLISHED) and msg_type not in hello_msgs:
            #     logger.error("Connection to {0} not established and got {1} message!  Closing."
            #                  .format(self.peer_desc, msg_type))
            #     self.state |= ConnectionState.MARK_FOR_CLOSE
            #     return 0

            logger.debug("Received message of type {0} from {1}".format(msg_type, self.peer_desc))

            if msg_type in self.message_handlers:
                msg_handler = self.message_handlers[msg_type]
                msg_handler(msg)

        logger.debug("Done receiving from {0}".format(self.peer_desc))
        return 0

    # Pop the next message off of the buffer given the message length.
    # Preserve invariant of self.inputbuf always containing the start of a valid message.
    def pop_next_message(self, payload_len, msg_type=Message, hdr_size=HDR_COMMON_OFF):
        try:
            msg_len = hdr_size + payload_len
            msg_contents = self.inputbuf.remove_bytes(msg_len)
            return msg_type.parse(msg_contents)
        except UnrecognizedCommandError as e:
            logger.error("Unrecognized command on {0}. Error Message: {1}".format(self.peer_desc, e.msg))
            logger.debug("Src: {0} Raw data: {1}".format(self.peer_desc, e.raw_data))
            return None

        except PayloadLenError as e:
            logger.error("ParseError on connection {0}.".format(self.peer_desc))
            logger.debug("ParseError message: {0}".format(e.msg))
            self.state |= ConnectionState.MARK_FOR_CLOSE  # Close, no retry.
            return None

    def get_bytes_on_buffer(self, buf, send_one_msg=False):
        if buf.has_more_bytes() > 0 and (not send_one_msg or buf.at_msg_boundary()):
            return buf.get_buffer()

    def advance_bytes_on_buffer(self, buf, bytes_written):
        buf.advance_buffer(bytes_written)

    def on_receive(self, bytes_received):
        self.inputbuf.add_bytes(bytes_received)
        self.recv()

    def get_bytes_to_send(self):
        return self.get_bytes_on_buffer(self.outputbuf)

    def on_sent(self, bytes_sent):
        self.advance_bytes_on_buffer(self.outputbuf, bytes_sent)

    def msg_hello(self, msg):
        self.state |= ConnectionState.HELLO_RECVD
        self.enqueue_msg(AckMessage())

        # Handle an Ack Message

    def msg_ack(self, msg):
        self.state |= ConnectionState.HELLO_ACKD

    def msg_ping(self, msg):
        self.enqueue_msg(PongMessage())

    def msg_pong(self, msg):
        pass

    # Receive a transaction assignment from txhash -> shortid
    def msg_txassign(self, msg):
        tx_hash = msg.tx_hash()

        logger.debug("Processing txassign message")
        if self.node.tx_service.get_txid(tx_hash) == -1:
            logger.debug("Assigning {0} to sid {1}".format(msg.tx_hash(), msg.short_id()))
            self.node.tx_service.assign_tx_to_sid(tx_hash, msg.short_id(), time.time())
            return tx_hash

        return None

    def close(self):
        pass
