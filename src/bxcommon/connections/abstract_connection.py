from abc import ABCMeta

from bxcommon.connections.connection_state import ConnectionState
from bxcommon.constants import MAX_BAD_MESSAGES, NULL_IDX
from bxcommon.exceptions import PayloadLenError, UnrecognizedCommandError
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.network.socket_connection import SocketConnection
from bxcommon.utils import logger
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.buffers.output_buffer import OutputBuffer
from bxcommon.utils.throughput.direction import Direction
from bxcommon.utils.throughput.throughput_service import throughput_service


class AbstractConnection(object):
    __metaclass__ = ABCMeta

    def __init__(self, socket_connection, address, node, from_me=False):
        if not isinstance(socket_connection, SocketConnection):
            raise ValueError("SocketConnection type is expected for socket_connection arg but was {0}."
                             .format(type(socket_connection)))

        self.socket_connection = socket_connection
        self.fileno = socket_connection.fileno()

        # (IP, Port) at time of socket creation. We may get a new application level port in
        # the version message if the connection is not from me.
        self.peer_ip, self.peer_port = address
        self.my_port = node.opts.external_port
        self.idx = NULL_IDX

        self.from_me = from_me  # Whether or not I initiated the connection

        self.outputbuf = OutputBuffer()
        self.inputbuf = InputBuffer()
        self.node = node

        self.state = ConnectionState.CONNECTING

        # Number of bad messages I've received in a row.
        self.num_bad_messages = 0
        self.peer_desc = "%s %d" % (self.peer_ip, self.peer_port)

        self.hello_messages = []
        self.header_size = 0
        self.message_factory = None
        self.message_handlers = None

    def add_received_bytes(self, bytes_received):
        """
        Adds bytes received from socket connection to input buffer

        :param bytes_received: new bytes received from socket connection
        :return:
        """

        assert not self.state & ConnectionState.MARK_FOR_CLOSE
        self.inputbuf.add_bytes(bytes_received)

    def get_bytes_to_send(self):
        assert not self.state & ConnectionState.MARK_FOR_CLOSE

        return self.get_bytes_on_buffer(self.outputbuf)

    def advance_sent_bytes(self, bytes_sent):
        self.advance_bytes_on_buffer(self.outputbuf, bytes_sent)

    def pre_process_msg(self):
        is_full_msg, msg_type, payload_len = self.message_factory.get_message_header_preview(self.inputbuf)
        logger.debug("Starting to get message of type {0}. Is full: {1}".format(msg_type, is_full_msg))
        return is_full_msg, msg_type, payload_len

    def enqueue_msg(self, msg):
        """
        Enqueues the contents of a Message instance, msg, to our outputbuf and attempts to send it if the underlying
        socket has room in the send buffer.

        :param msg: message
        """
        if self.state & ConnectionState.MARK_FOR_CLOSE:
            return

        self.enqueue_msg_bytes(msg.rawbytes())

    def enqueue_msg_bytes(self, msg_bytes):
        """
        Enqueues the raw bytes of a message, msg_bytes, to our outputbuf and attempts to send it if the
        underlying socket has room in the send buffer.

        :param msg_bytes: message bytes
        """

        if self.state & ConnectionState.MARK_FOR_CLOSE:
            return

        size = len(msg_bytes)

        logger.debug("Adding message of length {0} to {1}'s outputbuf".format(size, self.peer_desc))

        self.outputbuf.enqueue_msgbytes(msg_bytes)

        self.socket_connection.send()

    def process_message(self):
        """
        Processes the next bytes on the socket's inputbuffer.
        Returns 0 in order to avoid being rescheduled if this was an alarm.
        """
        while True:
            if self.state & ConnectionState.MARK_FOR_CLOSE:
                return 0

            is_full_msg, msg_type, payload_len = self.pre_process_msg()

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

            if not (self.state & ConnectionState.ESTABLISHED) and msg_type not in self.hello_messages:
                logger.error("Connection to {0} not established and got {1} message!  Closing."
                             .format(self.peer_desc, msg_type))
                self.state |= ConnectionState.MARK_FOR_CLOSE
                return 0

            throughput_service.add_event(Direction.INBOUND, msg_type, len(msg.rawbytes()), self.peer_desc)

            if msg_type in self.message_handlers:
                msg_handler = self.message_handlers[msg_type]
                msg_handler(msg)

        logger.debug("Done receiving from {0}".format(self.peer_desc))
        return 0

    def pop_next_message(self, payload_len):
        """
        Pop the next message off of the buffer given the message length.
        Preserve invariant of self.inputbuf always containing the start of a valid message.

        :param payload_len: length of payload
        :param msg_type: message type string
        :param hdr_size: size of header
        :return: message object
        """

        try:
            msg_len = self.header_size + payload_len
            msg_contents = self.inputbuf.remove_bytes(msg_len)
            return self.message_factory.create_message_from_buffer(msg_contents)
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
        throughput_service.add_event(Direction.OUTBOUND, None, bytes_written, self.peer_desc)
        buf.advance_buffer(bytes_written)

    def msg_hello(self, msg):
        self.state |= ConnectionState.HELLO_RECVD
        self.enqueue_msg(AckMessage())

    def msg_ack(self, msg):
        """
        Handle an Ack Message
        """
        self.state |= ConnectionState.HELLO_ACKD

    def msg_ping(self, msg):
        self.enqueue_msg(PongMessage())

    def msg_pong(self, msg):
        pass

    def mark_for_close(self):
        self.state |= ConnectionState.MARK_FOR_CLOSE
