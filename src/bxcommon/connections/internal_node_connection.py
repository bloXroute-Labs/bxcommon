from abc import ABCMeta
from datetime import datetime

from bxutils import logging

from bxcommon.connections.abstract_connection import AbstractConnection, Node
from bxcommon.connections.connection_state import ConnectionState
from bxcommon import constants
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.utils import nonce_generator
from bxcommon.utils.buffers.output_buffer import OutputBuffer
from bxcommon.utils.expiring_dict import ExpiringDict
from bxcommon.utils.stats import hooks
from bxcommon.utils.stats.measurement_type import MeasurementType

logger = logging.get_logger(__name__)


class InternalNodeConnection(AbstractConnection[Node]):
    __metaclass__ = ABCMeta

    def __init__(self, sock, address, node, from_me=False):
        super(InternalNodeConnection, self).__init__(sock, address, node, from_me)

        # Enable buffering only on internal connections
        self.enable_buffered_send = node.opts.enable_buffered_send
        self.outputbuf = OutputBuffer(enable_buffering=self.enable_buffered_send)

        self.network_num = node.network_num
        self.version_manager = bloxroute_version_manager

        # Setting default protocol version and message factory; override when hello message received
        self.message_factory = bloxroute_message_factory
        self.protocol_version = self.version_manager.CURRENT_PROTOCOL_VERSION

        self.ping_message = PingMessage()
        self.pong_message = PongMessage()
        self.ack_message = AckMessage()

        self.can_send_pings = True
        self.sent_response_messages_timestamps = ExpiringDict(self.node.alarm_queue, constants.REQUEST_EXPIRATION_TIME)

    def disable_buffering(self):
        """
        Disable buffering on this particular connection.
        :return:
        """
        self.enable_buffered_send = False
        self.outputbuf.flush()
        self.outputbuf.enable_buffering = False
        self.socket_connection.send()

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
            logger.warning(
                "Protocol version {} of remote node '{}' is not supported. Closing connection.",
                protocol_version,
                self.peer_desc
            )
            self.mark_for_close()
            return False

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

        if self.state & ConnectionState.MARK_FOR_CLOSE:
            logger.debug("Connection has been closed: {}, Ignoring: {} ", self, msg)
            return

        network_num = msg.network_num()

        if self.node.network_num != constants.ALL_NETWORK_NUM and network_num != self.node.network_num:
            logger.error("Network number mismatch. Current network num {}, remote network num {}. Closing connection."
                         .format(self.node.network_num, network_num))
            self.mark_for_close()
            return

        self.network_num = network_num
        self.node.alarm_queue.register_alarm(self.ping_interval_s, self.send_ping)
        logger.debug("Received Hello message from peer with network number '{}'.".format(network_num))

    def peek_broadcast_msg_network_num(self, input_buffer):

        if self.protocol_version == 1:
            return constants.DEFAULT_NETWORK_NUM

        return BroadcastMessage.peek_network_num(input_buffer)

    def send_ping(self):
        """
        Send a ping (and reschedule if called from alarm queue)
        """
        if self.can_send_pings and not self.state & ConnectionState.MARK_FOR_CLOSE:
            nonce = nonce_generator.get_nonce()
            msg = PingMessage(nonce=nonce)
            self.enqueue_msg(msg)
            self.sent_response_messages_timestamps.add(nonce, msg.timestamp)
            return self.ping_interval_s
        return constants.CANCEL_ALARMS

    def msg_ping(self, msg):
        nonce = msg.nonce()
        self.enqueue_msg(PongMessage(nonce=nonce))

    def msg_pong(self, msg):
        nonce = msg.nonce()
        if nonce in self.sent_response_messages_timestamps.contents:
            request_msg_timestamp = self.sent_response_messages_timestamps.contents[nonce]
            request_response_time = (datetime.utcnow() - request_msg_timestamp).total_seconds()
            logger.debug("Ping-pong for nonce {} response time: {} on connection: {}"
                         .format(msg.nonce(), request_response_time, self))
            hooks.add_measurement(self.peer_desc, MeasurementType.PING, request_response_time)
        elif nonce is not None:
            logger.warning("Received pong message from {} {} with nonce {}, ping request was not found in cache"
                        .format(self.peer_desc, self.CONNECTION_TYPE, nonce))
