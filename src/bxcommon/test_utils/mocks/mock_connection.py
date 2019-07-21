from enum import IntFlag

from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.constants import PING_INTERVAL_S
from bxcommon.network.socket_connection import SocketConnection
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.buffers.output_buffer import OutputBuffer


class MockConnectionType(IntFlag):
    MOCK = max(ConnectionType) << 1
    NOT_MOCK = max(ConnectionType) << 2


class MockConnection:
    CONNECTION_TYPE = MockConnectionType.MOCK

    def __init__(self, sock: SocketConnection, address, node, from_me=False):
        self.socket_connection = sock
        self.fileno = sock.fileno()

        # (IP, Port) at time of socket creation. We may get a new application level port in
        # the version message if the connection is not from me.
        self.peer_ip, self.peer_port = address
        self.peer_id = None
        self.my_ip = node.opts.external_ip
        self.my_port = node.opts.external_port

        self.from_me = from_me  # Whether or not I initiated the connection

        self.outputbuf = OutputBuffer()
        self.inputbuf = InputBuffer()
        self.node = node

        self.is_persistent = False
        self.state = ConnectionState.CONNECTING

        # Number of bad messages I've received in a row.
        self.num_bad_messages = 0
        self.peer_desc = "%s %d" % (self.peer_ip, self.peer_port)
        self.message_handlers = None
        self.network_num = node.opts.blockchain_network_num

    def is_active(self):
        return self.state & ConnectionState.ESTABLISHED == ConnectionState.ESTABLISHED and \
               not self.state & ConnectionState.MARK_FOR_CLOSE

    def mark_for_close(self, force_destroy_now=False):
        self.state |= ConnectionState.MARK_FOR_CLOSE

    def add_received_bytes(self, bytes_received):
        self.inputbuf.add_bytes(bytes_received)
        self.mark_for_close()

    def get_bytes_to_send(self):
        return self.outputbuf.output_msgs[0]

    def advance_sent_bytes(self, bytes_sent):
        self.advance_bytes_on_buffer(self.outputbuf, bytes_sent)

    def advance_bytes_on_buffer(self, buf, bytes_written):
        buf.advance_buffer(bytes_written)

    def enqueue_msg(self, msg, _prepend_to_queue=False):

        if self.state & ConnectionState.MARK_FOR_CLOSE:
            return

        self.outputbuf.enqueue_msgbytes(msg.rawbytes())

    def enqueue_msg_bytes(self, msg_bytes, prepend=False):

        if self.state & ConnectionState.MARK_FOR_CLOSE:
            return

        self.outputbuf.enqueue_msgbytes(msg_bytes)

    def process_message(self):
        pass

    def send_ping(self):
        return PING_INTERVAL_S
