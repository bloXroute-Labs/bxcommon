from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.constants import ALL_NETWORK_NUM, DEFAULT_NETWORK_NUM
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.utils import logger


class InternalNodeConnection(AbstractConnection):

    def __init__(self, sock, address, node, from_me=False):
        super(InternalNodeConnection, self).__init__(sock, address, node, from_me)

        self.network_num = node.network_num
        self.version_manager = bloxroute_version_manager
        
        # Setting default protocol version and message factory; override when hello message received
        self.message_factory = bloxroute_message_factory
        self.protocol_version = self.version_manager.CURRENT_PROTOCOL_VERSION

        self.ping_message = PingMessage()
        self.pong_message = PongMessage()
        self.ack_message = AckMessage()

    def set_protocol_version_and_message_factory(self):
        """
        Gets protocol version from the first bytes of hello message if not known.
        Sets protocol version and creates message factory for that protocol version
        """

        # Outgoing connections use current version of protocol and message factory
        if self.from_me or self.state & ConnectionState.HELLO_RECVD:
            return True

        protocol_version = self.version_manager.get_connection_protocol_version(self.inputbuf)

        if protocol_version is None:
            return False

        if not self.version_manager.is_protocol_supported(protocol_version):
            logger.error("Protocol version of remote node '{}' is not supported. Closing connection."
                         .format(protocol_version))
            self.mark_for_close()
            return

        self.protocol_version = protocol_version
        self.message_factory = self.version_manager.get_message_factory_for_version(protocol_version)

        logger.debug("Detected incoming connection with protocol version {}".format(protocol_version))

        return True

    def pre_process_msg(self):
        success = self.set_protocol_version_and_message_factory()

        if not success:
            return False, None, None

        return super(InternalNodeConnection, self).pre_process_msg()

    def enqueue_msg(self, msg, prepend=False):
        if self.state & ConnectionState.MARK_FOR_CLOSE:
            return

        if self.protocol_version < self.version_manager.CURRENT_PROTOCOL_VERSION:
            versioned_message = self.version_manager.convert_message_to_older_version(self.protocol_version, msg)
        else:
            versioned_message = msg

        super(InternalNodeConnection, self).enqueue_msg(versioned_message, prepend)

    def pop_next_message(self, payload_len):
        msg = super(InternalNodeConnection, self).pop_next_message(payload_len)

        if msg is None or self.protocol_version >= self.version_manager.CURRENT_PROTOCOL_VERSION:
            return msg

        versioned_msg = self.version_manager.convert_message_from_older_version(self.protocol_version, msg)

        return versioned_msg

    def msg_hello(self, msg):
        super(InternalNodeConnection, self).msg_hello(msg)

        network_num = msg.network_num()

        if self.node.network_num != ALL_NETWORK_NUM and network_num != self.node.network_num:
            logger.error("Network number mismatch. Current network num {}, remote network num {}. Closing connection.")
            self.mark_for_close()
            return

        self.network_num = network_num

        logger.debug("Received Hello message from peer with network number '{}'.".format(network_num))

    def peek_broadcast_msg_network_num(self, input_buffer):

        if self.protocol_version == 1:
            return DEFAULT_NETWORK_NUM

        return BroadcastMessage.peek_network_num(input_buffer)