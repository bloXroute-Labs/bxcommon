from typing import Optional, Set, Union

from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.constants import PING_INTERVAL_S
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.messages.abstract_message_factory import AbstractMessageFactory
from bxcommon.network.abstract_socket_connection_protocol import AbstractSocketConnectionProtocol
from bxcommon.network.network_direction import NetworkDirection
from bxcommon.utils import memory_utils
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.buffers.output_buffer import OutputBuffer
from bxcommon.utils.memory_utils import SpecialMemoryProperties, SpecialTuple
from bxcommon.models.broadcast_message_type import BroadcastMessageType


class MockConnection(AbstractConnection, SpecialMemoryProperties):
    CONNECTION_TYPE = ConnectionType.EXTERNAL_GATEWAY

    # pylint: disable=super-init-not-called
    def __init__(self, sock: AbstractSocketConnectionProtocol, node) -> None:
        self.socket_connection = sock
        self.file_no = sock.file_no

        # (IP, Port) at time of socket creation. We may get a new application level port in
        # the version message if the connection is not from me.
        self.peer_ip, self.peer_port = sock.endpoint
        self.endpoint = sock.endpoint
        self.peer_id = None
        self.my_ip = node.opts.external_ip
        self.my_port = node.opts.external_port
        self.direction = self.socket_connection.direction

        self.from_me = self.direction == NetworkDirection.OUTBOUND  # Whether or not I initiated the connection

        self.outputbuf = OutputBuffer()
        self.inputbuf = InputBuffer()
        self.node = node

        self.is_persistent = False
        self.state = ConnectionState.CONNECTING
        self.established = False

        # Number of bad messages I've received in a row.
        self.num_bad_messages = 0
        self.peer_desc = "{} {}".format(self.peer_ip, self.peer_port)
        self.message_handlers = None
        self.network_num = node.opts.blockchain_network_num
        self.format_connection()

        self.enqueued_messages = []
        self.node_privileges = "general"
        self.subscribed_broadcasts = [BroadcastMessageType.BLOCK]
        self.ping_alarm_id = None

    def __repr__(self):
        return f"MockConnection<file_no: {self.file_no}, address: ({self.peer_ip}, {self.peer_port}), " \
            f"network_num: {self.network_num}>"

    def connection_message_factory(self) -> AbstractMessageFactory:
        pass

    def ping_message(self) -> AbstractMessage:
        pass

    def add_received_bytes(self, bytes_received):
        self.inputbuf.add_bytes(bytes_received)
        self.mark_for_close()

    def get_bytes_to_send(self):
        return self.outputbuf.output_msgs[0]

    def advance_sent_bytes(self, bytes_sent):
        self.advance_bytes_on_buffer(self.outputbuf, bytes_sent)

    def advance_bytes_on_buffer(self, buf, bytes_written):
        buf.advance_buffer(bytes_written)

    def enqueue_msg(self, msg: AbstractMessage, prepend: bool = False):
        if not self.is_alive():
            return

        self.outputbuf.enqueue_msgbytes(msg.rawbytes())
        self.enqueued_messages.append(msg)

    def enqueue_msg_bytes(
        self,
        msg_bytes: Union[bytearray, memoryview],
        prepend: bool = False,
    ):
        if not self.is_alive():
            return

        self.outputbuf.enqueue_msgbytes(msg_bytes)
        self.enqueued_messages.append(msg_bytes)

    def process_message(self):
        pass

    def send_ping(self):
        return PING_INTERVAL_S

    def special_memory_size(self, ids: Optional[Set[int]] = None) -> SpecialTuple:
        return memory_utils.add_special_objects(self.inputbuf, self.outputbuf, ids=ids)
