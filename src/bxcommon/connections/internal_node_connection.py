import time
from abc import ABCMeta
from typing import List, Optional, Dict

from bxcommon import constants
from bxcommon.connections.abstract_connection import AbstractConnection, Node
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.messages.bloxroute import txs_serializer
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.blocks_short_ids_serializer import BlockShortIds
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.bloxroute_message_validator import BloxrouteMessageValidator
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.tx_service_sync_blocks_short_ids_message import TxServiceSyncBlocksShortIdsMessage
from bxcommon.messages.bloxroute.tx_service_sync_complete_message import TxServiceSyncCompleteMessage
from bxcommon.messages.bloxroute.tx_service_sync_req_message import TxServiceSyncReqMessage
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import TxServiceSyncTxsMessage
from bxcommon.messages.bloxroute.txs_serializer import TxContentShortIds
from bxcommon.models.node_type import NodeType
from bxcommon.models.quota_type_model import QuotaType
from bxcommon.network.abstract_socket_connection_protocol import AbstractSocketConnectionProtocol
from bxcommon.utils import nonce_generator, performance_utils
from bxcommon.utils.buffers.output_buffer import OutputBuffer
from bxcommon.utils.expiring_dict import ExpiringDict
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.utils.stats import hooks
from bxcommon.utils.stats.measurement_type import MeasurementType
from bxutils import logging
from bxutils.logging import LogRecordType

logger = logging.get_logger(__name__)
performance_troubleshooting_logger = logging.get_logger(LogRecordType.PerformanceTroubleshooting, __name__)


class InternalNodeConnection(AbstractConnection[Node]):
    __metaclass__ = ABCMeta

    def __init__(self, sock: AbstractSocketConnectionProtocol, node: Node):
        super(InternalNodeConnection, self).__init__(sock, node)

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
        self.ping_message_timestamps = ExpiringDict(self.node.alarm_queue, constants.REQUEST_EXPIRATION_TIME)
        self._sync_ping_latencies: Dict[int, Optional[float]] = {}
        self._nonce_to_network_num: Dict[int, int] = {}
        self.message_validator = BloxrouteMessageValidator(None, self.protocol_version)

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
            logger.debug(
                "Got message protocol {} that is higher the current version {}. Using current protocol version",
                protocol_version, self.version_manager.CURRENT_PROTOCOL_VERSION)
            protocol_version = self.version_manager.CURRENT_PROTOCOL_VERSION

        self.protocol_version = protocol_version
        self.message_factory = self.version_manager.get_message_factory_for_version(protocol_version)

        self.log_trace("Setting connection protocol version to {}".format(protocol_version))

        return True

    def pre_process_msg(self):
        success = self.set_protocol_version_and_message_factory()

        if not success:
            return False, None, None

        return super(InternalNodeConnection, self).pre_process_msg()

    def enqueue_msg(self, msg, prepend=False):
        if not self.is_alive():
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

        if not self.is_alive():
            self.log_trace("Connection has been closed: {}, Ignoring: {} ", self, msg)
            return

        network_num = msg.network_num()

        if self.node.network_num != constants.ALL_NETWORK_NUM and network_num != self.node.network_num:
            self.log_warning(
                "Network number mismatch. Current network num {}, remote network num {}. Closing connection.",
                self.node.network_num, network_num)
            self.mark_for_close()
            return

        self.network_num = network_num
        self.node.alarm_queue.register_alarm(self.ping_interval_s, self.send_ping)

    def peek_broadcast_msg_network_num(self, input_buffer):

        if self.protocol_version == 1:
            return constants.DEFAULT_NETWORK_NUM

        return BroadcastMessage.peek_network_num(input_buffer)

    def send_ping(self):
        """
        Send a ping (and reschedule if called from alarm queue)
        """
        if self._send_ping() is not None:
            return self.ping_interval_s
        return constants.CANCEL_ALARMS

    def msg_ping(self, msg):
        nonce = msg.nonce()
        self.enqueue_msg(PongMessage(nonce=nonce))

    def msg_pong(self, msg: PongMessage):
        nonce = msg.nonce()
        if nonce in self.ping_message_timestamps.contents:
            request_msg_timestamp = self.ping_message_timestamps.contents[nonce]
            request_response_time = time.time() - request_msg_timestamp
            if nonce in self._nonce_to_network_num:
                self._sync_ping_latencies[self._nonce_to_network_num[nonce]] = request_response_time
            self.log_trace("Pong for nonce {} had response time: {}", msg.nonce(), request_response_time)
            hooks.add_measurement(self.peer_desc, MeasurementType.PING, request_response_time)
        elif nonce is not None:
            self.log_debug("Pong message had no matching ping request. Nonce: {}", nonce)

        self.cancel_pong_timeout()

    def msg_tx_service_sync_txs(self, msg: TxServiceSyncTxsMessage):
        """
        Transaction service sync message receive txs data
        """
        network_num = msg.network_num()
        self.node.last_sync_message_received_by_network[network_num] = time.time()
        tx_service = self.node.get_tx_service(network_num)
        txs_content_short_ids = msg.txs_content_short_ids()

        for tx_content_short_ids in txs_content_short_ids:
            tx_hash = tx_content_short_ids.tx_hash
            tx_service.set_transaction_contents(tx_hash, tx_content_short_ids.tx_content)
            for short_id, quota_type in zip(tx_content_short_ids.short_ids, tx_content_short_ids.short_id_flags):
                tx_service.assign_short_id(tx_hash, short_id)
                if QuotaType.PAID_DAILY_QUOTA in quota_type:
                    tx_service.set_short_id_quota_type(short_id, quota_type)

    def _create_txs_service_msg(self, network_num: int, tx_service_snap: List[Sha256Hash]) -> List[TxContentShortIds]:
        txs_content_short_ids: List[TxContentShortIds] = []
        txs_msg_len = 0
        tx_service = self.node.get_tx_service(network_num)
        while tx_service_snap:
            tx_hash = tx_service_snap.pop()
            short_ids = tx_service.get_short_ids(tx_hash)
            # TODO: evaluate short id quota type flag value
            short_id_flags = [tx_service.get_short_id_quota_type(short_id) for short_id in short_ids]
            tx_content_short_ids: TxContentShortIds = TxContentShortIds(
                tx_hash,
                self.node.get_tx_service(network_num).get_transaction_by_hash(tx_hash),
                list(short_ids),
                short_id_flags
            )

            txs_msg_len += txs_serializer.get_serialized_tx_content_short_ids_bytes_len(tx_content_short_ids)

            txs_content_short_ids.append(tx_content_short_ids)
            if txs_msg_len >= constants.TXS_MSG_SIZE:
                break

        return txs_content_short_ids

    def send_tx_service_sync_req(self, network_num: int):
        """
        sending transaction service sync request
        """
        self.node.last_sync_message_received_by_network[network_num] = time.time()
        self.enqueue_msg(TxServiceSyncReqMessage(network_num))

    def send_tx_service_sync_complete(self, network_num: int):
        if network_num in self._sync_ping_latencies:
            del self._sync_ping_latencies[network_num]
        self._nonce_to_network_num = {
            nonce: other_network_num for nonce, other_network_num in self._nonce_to_network_num.items()
            if other_network_num != network_num
        }

        self.enqueue_msg(TxServiceSyncCompleteMessage(network_num))

    def send_tx_service_sync_blocks_short_ids(self, network_num: int):
        blocks_short_ids: List[BlockShortIds] = []
        start_time = time.time()
        for block_hash, short_ids in self.node.get_tx_service(network_num).iter_short_ids_seen_in_block():
            blocks_short_ids.append(BlockShortIds(block_hash, short_ids))

        block_short_ids_msg = TxServiceSyncBlocksShortIdsMessage(network_num, blocks_short_ids)
        performance_utils.log_operation_duration(
            performance_troubleshooting_logger,
            "Create tx service sync block short ids message",
            start_time,
            constants.RESPONSIVENESS_CHECK_DELAY_WARN_THRESHOLD_S,
            network_num=network_num,
            connection=self,
            blocks_short_ids_count=len(blocks_short_ids)
        )
        duration = time.time() - start_time
        self.log_trace("Sending {} block short ids took {:.3f} seconds.", len(blocks_short_ids), duration)
        self.enqueue_msg(block_short_ids_msg)

    def send_tx_service_sync_txs(self, network_num: int, tx_service_snap: List[Sha256Hash], duration: float = 0,
                                 msgs_count: int = 0, total_tx_count: int = 0, sending_tx_msgs_start_time: float = 0):
        sync_ping_latency = self._sync_ping_latencies.get(network_num, 0.0)
        if (time.time() - sending_tx_msgs_start_time) < constants.SENDING_TX_MSGS_TIMEOUT_MS:
            if tx_service_snap and sync_ping_latency is not None:
                start = time.time()
                txs_content_short_ids = self._create_txs_service_msg(network_num, tx_service_snap)
                performance_utils.log_operation_duration(
                    performance_troubleshooting_logger,
                    "Create tx service sync message",
                    start,
                    constants.RESPONSIVENESS_CHECK_DELAY_WARN_THRESHOLD_S,
                    network_num=network_num,
                    connection=self,
                    tx_count=len(txs_content_short_ids)
                )
                self.enqueue_msg(TxServiceSyncTxsMessage(network_num, txs_content_short_ids))
                nonce = self._send_ping()
                if nonce is not None:
                    self._nonce_to_network_num[nonce] = network_num
                    self._sync_ping_latencies[network_num] = None
                duration += time.time() - start
                msgs_count += 1
                total_tx_count += len(txs_content_short_ids)
            # checks again if tx_snap in case we still have msgs to send, else no need to wait
            # for the next interval.
            if tx_service_snap:
                if sync_ping_latency is None:
                    next_interval = constants.TX_SERVICE_SYNC_TXS_S
                else:
                    next_interval = max(sync_ping_latency * 0.5, constants.TX_SERVICE_SYNC_TXS_S)
                self.node.alarm_queue.register_alarm(
                    next_interval, self.send_tx_service_sync_txs, network_num, tx_service_snap,
                    duration, msgs_count, total_tx_count, sending_tx_msgs_start_time
                )
            else:  # if all txs were sent, send complete msg
                self.log_debug(
                    "Sending {} transactions and {} messages of network: {} took {:.3f} seconds.",
                    total_tx_count,
                    msgs_count,
                    network_num,
                    duration
                )
                self.send_tx_service_sync_complete(network_num)
        else:  # if time is up - upgrade this node as synced - giving up
            self.log_debug(
                "Sending {} transactions and {} messages of network: {} took more than {} seconds. Giving up.",
                total_tx_count,
                msgs_count,
                network_num,
                constants.SENDING_TX_MSGS_TIMEOUT_MS
            )
            self.send_tx_service_sync_complete(network_num)

    def msg_tx_service_sync_complete(self, msg: TxServiceSyncCompleteMessage):
        if self.node.NODE_TYPE in NodeType.GATEWAY and ConnectionType.RELAY_BLOCK in self.CONNECTION_TYPE:
            return
        network_num = msg.network_num()
        self.node.last_sync_message_received_by_network.pop(network_num, None)
        self.log_info(
            "{} is ready and operational. It took {:.3f} seconds to complete transaction state with BDN.",
            self.node.NODE_TYPE, time.time() - self.node.start_sync_time
        )
        self.node.on_fully_updated_tx_service()

    def mark_for_close(self, should_retry: Optional[bool] = None):
        super(InternalNodeConnection, self).mark_for_close(should_retry)
        self.cancel_pong_timeout()

    def _send_ping(self) -> Optional[int]:
        if self.can_send_pings and self.is_alive():
            nonce = nonce_generator.get_nonce()
            msg = PingMessage(nonce=nonce)
            self.enqueue_msg(msg)
            self.ping_message_timestamps.add(nonce, time.time())

            self.schedule_pong_timeout()
            return nonce
        else:
            return None
