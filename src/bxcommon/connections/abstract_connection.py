from bxcommon.connections.connection_state import ConnectionState
from bxcommon.constants import HDR_COMMON_OFF, MAX_BAD_MESSAGES, NULL_IDX
from bxcommon.exceptions import PayloadLenError, UnrecognizedCommandError
from bxcommon.messages.ack_message import AckMessage
from bxcommon.messages.message import Message
from bxcommon.messages.pong_message import PongMessage
from bxcommon.utils import logger
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.buffers.output_buffer import OutputBuffer
from bxcommon.utils.throughput.direction import Direction
from bxcommon.utils.throughput.throughput_service import throughput_service


class AbstractConnection(object):
    def __init__(self, fileno, address, node, from_me=False):
        self.fileno = fileno

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

        self.message_handlers = None

        throughput_service.set_node(self.node)

    def add_received_bytes(self, bytes_received):
        assert not self.state & ConnectionState.MARK_FOR_CLOSE

        self.inputbuf.add_bytes(bytes_received)
        self.process_message()

    def get_bytes_to_send(self):
        assert not self.state & ConnectionState.MARK_FOR_CLOSE

        return self.get_bytes_on_buffer(self.outputbuf)

    def advance_sent_bytes(self, bytes_sent):
        self.advance_bytes_on_buffer(self.outputbuf, bytes_sent)

    def pre_process_msg(self, msg_cls):
        is_full_msg, msg_type, payload_len = msg_cls.peek_message(self.inputbuf)

        logger.debug("XXX: Starting to get message of type {0}. Is full: {1}".format(msg_type, is_full_msg))

        return is_full_msg, msg_type, payload_len

    def enqueue_msg(self, msg):
        """
        Enqueues the contents of a Message instance, msg, to our outputbuf and attempts to send it if the underlying
        socket has room in the send buffer.

        :param msg: message
        """
        if self.state & ConnectionState.MARK_FOR_CLOSE:
            return

        self.outputbuf.enqueue_msgbytes(msg.rawbytes())

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

    def process_message(self, msg_cls=Message, hello_msgs=['hello', 'ack']):
        """
        Receives and processes the next bytes on the socket's inputbuffer.
        Returns 0 in order to avoid being rescheduled if this was an alarm.

        :param msg_cls: class of message
        :param hello_msgs: list of hello messages types
        """

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

            if not (self.state & ConnectionState.ESTABLISHED) and msg_type not in hello_msgs:
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

    def pop_next_message(self, payload_len, msg_type=Message, hdr_size=HDR_COMMON_OFF):
        """
        Pop the next message off of the buffer given the message length.
        Preserve invariant of self.inputbuf always containing the start of a valid message.

        :param payload_len: length of payload
        :param msg_type: message type string
        :param hdr_size: size of header
        :return: message object
        """

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
