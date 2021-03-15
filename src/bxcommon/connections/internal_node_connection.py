import time
from abc import ABCMeta
from typing import Optional, Dict, cast

from bxcommon import constants
from bxcommon.connections.abstract_connection import AbstractConnection, Node, \
    ConnectionMessagePreview
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.messages.abstract_message_factory import AbstractMessageFactory
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.bloxroute_message_validator import BloxrouteMessageValidator
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.network.abstract_socket_connection_protocol import AbstractSocketConnectionProtocol
from bxcommon.utils import nonce_generator
from bxcommon.utils.buffers.output_buffer import OutputBuffer
from bxcommon.utils.expiring_dict import ExpiringDict
from bxcommon.utils.stats import hooks
from bxcommon.utils.stats.measurement_type import MeasurementType
from bxcommon.services.tx_sync_service import TxSyncService

from bxutils import log_messages
from bxutils import logging


logger = logging.get_logger(__name__)


class InternalNodeConnection(AbstractConnection[Node]):
    __metaclass__ = ABCMeta

    def __init__(self, sock: AbstractSocketConnectionProtocol, node: Node) -> None:
        super(InternalNodeConnection, self).__init__(sock, node)

        # Enable buffering only on internal connections
        self.enable_buffered_send = node.opts.enable_buffered_send
        self.outputbuf = OutputBuffer(enable_buffering=self.enable_buffered_send)

        self.network_num = node.network_num
        self.version_manager = bloxroute_version_manager

        # Setting default protocol version; override when hello message received
        self.protocol_version = self.version_manager.CURRENT_PROTOCOL_VERSION

        self.pong_message = PongMessage()
        self.ack_message = AckMessage()

        self.can_send_pings = True
        self.pong_timeout_enabled = True

        self.ping_message_timestamps = ExpiringDict(
            self.node.alarm_queue,
            constants.REQUEST_EXPIRATION_TIME,
            f"{str(self)}_ping_timestamps"
        )

        self.sync_ping_latencies: Dict[int, Optional[float]] = {}
        self._nonce_to_network_num: Dict[int, int] = {}
        self.message_validator = BloxrouteMessageValidator(None, self.protocol_version)
        self.tx_sync_service = TxSyncService(self)
        self.inbound_peer_latency: float = time.time()

    def connection_message_factory(self) -> AbstractMessageFactory:
        return bloxroute_message_factory

    def ping_message(self) -> AbstractMessage:
        nonce = nonce_generator.get_nonce()
        self.ping_message_timestamps.add(nonce, time.time())
        return PingMessage(nonce)

    def disable_buffering(self):
        """
        Disable buffering on this particular connection.
        :return:
        """
        self.enable_buffered_send = False
        self.outputbuf.flush()
        self.outputbuf.enable_buffering = False
        self.socket_connection.send()

    def set_protocol_version_and_message_factory(self) -> bool:
        """
        Gets protocol version from the first bytes of hello message if not known.
        Sets protocol version and creates message factory for that protocol version
        """

        # Outgoing connections use current version of protocol and message factory
        if ConnectionState.HELLO_RECVD in self.state:
            return True

        protocol_version = self.version_manager.get_connection_protocol_version(self.inputbuf)

        if protocol_version is None:
            return False

        if not self.version_manager.is_protocol_supported(protocol_version):
            self.log_debug(
                "Protocol version {} of remote node '{}' is not supported. Closing connection.",
                protocol_version,
                self.peer_desc
            )
            self.mark_for_close()
            return False

        if protocol_version > self.version_manager.CURRENT_PROTOCOL_VERSION:
            self.log_debug(
                "Got message protocol {} that is higher the current version {}. Using current protocol version",
                protocol_version, self.version_manager.CURRENT_PROTOCOL_VERSION)
            protocol_version = self.version_manager.CURRENT_PROTOCOL_VERSION

        self.protocol_version = protocol_version
        self.message_factory = self.version_manager.get_message_factory_for_version(protocol_version)

        self.log_trace("Setting connection protocol version to {}".format(protocol_version))

        return True

    def pre_process_msg(self) -> ConnectionMessagePreview:
        success = self.set_protocol_version_and_message_factory()

        if not success:
            return ConnectionMessagePreview(False, True, None, None)

        return super(InternalNodeConnection, self).pre_process_msg()

    def enqueue_msg(self, msg, prepend=False):
        if not self.is_alive():
            return

        if self.protocol_version < self.version_manager.CURRENT_PROTOCOL_VERSION:
            versioned_message = self.version_manager.convert_message_to_older_version(self.protocol_version, msg)
        else:
            versioned_message = msg

        super(InternalNodeConnection, self).enqueue_msg(versioned_message, prepend)

    def pop_next_message(self, payload_len: int) -> AbstractMessage:
        msg = super(InternalNodeConnection, self).pop_next_message(payload_len)

        if msg is None or self.protocol_version >= self.version_manager.CURRENT_PROTOCOL_VERSION:
            return msg

        versioned_msg = self.version_manager.convert_message_from_older_version(self.protocol_version, msg)

        return versioned_msg

    def check_ping_latency_for_network(self, network_num: int) -> None:
        ping_message = cast(PingMessage, self.ping_message())
        self.enqueue_msg(ping_message)
        self._nonce_to_network_num[ping_message.nonce()] = network_num
        self.sync_ping_latencies[network_num] = None

    def msg_hello(self, msg):
        super(InternalNodeConnection, self).msg_hello(msg)

        if not self.is_alive():
            self.log_trace("Connection has been closed: {}, Ignoring: {} ", self, msg)
            return

        network_num = msg.network_num()

        if self.node.network_num != constants.ALL_NETWORK_NUM and network_num != self.node.network_num:
            self.log_warning(log_messages.NETWORK_NUMBER_MISMATCH, self.node.network_num, network_num)
            self.mark_for_close()
            return

        self.network_num = network_num

        self.schedule_pings()

    def peek_broadcast_msg_network_num(self, input_buffer):

        if self.protocol_version == 1:
            return constants.DEFAULT_NETWORK_NUM

        return BroadcastMessage.peek_network_num(input_buffer)

    # pylint: disable=arguments-differ
    def msg_ping(self, msg: PingMessage):
        nonce = msg.nonce()
        assumed_request_time = time.time() - nonce_generator.get_timestamp_from_nonce(nonce)
        self.inbound_peer_latency = assumed_request_time
        hooks.add_measurement(self.peer_desc, MeasurementType.PING_INCOMING, assumed_request_time, self.peer_id)

        self.enqueue_msg(PongMessage(nonce=nonce, timestamp=nonce_generator.get_nonce()))

    # pylint: disable=arguments-differ
    def msg_pong(self, msg: PongMessage):
        super(InternalNodeConnection, self).msg_pong(msg)

        nonce = msg.nonce()
        timestamp = msg.timestamp()
        if timestamp:
            self.inbound_peer_latency = time.time() - nonce_generator.get_timestamp_from_nonce(timestamp)
        if nonce in self.ping_message_timestamps.contents:
            request_msg_timestamp = self.ping_message_timestamps.contents[nonce]
            request_response_time = time.time() - request_msg_timestamp

            if nonce in self._nonce_to_network_num:
                self.sync_ping_latencies[self._nonce_to_network_num[nonce]] = request_response_time

            if request_response_time > constants.PING_PONG_TRESHOLD:
                self.log_debug(
                    "Ping/pong exchange nonce {} took {:.2f} seconds to complete.",
                    msg.nonce(),
                    request_response_time
                )
            else:
                self.log_trace(
                    "Ping/pong exchange nonce {} took {:.2f} seconds to complete.",
                    msg.nonce(),
                    request_response_time
                )

            hooks.add_measurement(self.peer_desc, MeasurementType.PING, request_response_time, self.peer_id)
            if timestamp:
                assumed_peer_response_time = nonce_generator.get_timestamp_from_nonce(timestamp) - request_msg_timestamp
                hooks.add_measurement(
                    self.peer_desc, MeasurementType.PING_OUTGOING, assumed_peer_response_time, self.peer_id
                )

        elif nonce is not None:
            self.log_debug("Pong message had no matching ping request. Nonce: {}", nonce)

    def mark_for_close(self, should_retry: Optional[bool] = None):
        super(InternalNodeConnection, self).mark_for_close(should_retry)
        self.cancel_pong_timeout()

    def is_gateway_connection(self):
        return self.CONNECTION_TYPE in ConnectionType.GATEWAY

    def is_external_gateway_connection(self):
        # self.CONNECTION_TYPE == ConnectionType.GATEWAY is equal True only for V1 gateways
        return self.CONNECTION_TYPE in ConnectionType.EXTERNAL_GATEWAY or self.CONNECTION_TYPE == ConnectionType.GATEWAY

    def is_internal_gateway_connection(self) -> bool:
        return self.CONNECTION_TYPE in ConnectionType.INTERNAL_GATEWAY

    def is_relay_connection(self):
        return self.CONNECTION_TYPE in ConnectionType.RELAY_ALL

    def is_proxy_connection(self) -> bool:
        return self.CONNECTION_TYPE in ConnectionType.RELAY_PROXY

    def update_tx_sync_complete(self, network_num: int):
        if network_num in self.sync_ping_latencies:
            del self.sync_ping_latencies[network_num]
        self._nonce_to_network_num = {
            nonce: other_network_num
            for nonce, other_network_num in self._nonce_to_network_num.items()
            if other_network_num != network_num
        }
