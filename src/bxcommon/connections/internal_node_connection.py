from abc import ABCMeta
from datetime import datetime
from typing import List
import time

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
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import TxServiceSyncTxsMessage
from bxcommon.messages.bloxroute.tx_service_sync_req_message import TxServiceSyncReqMessage
from bxcommon.messages.bloxroute.tx_service_sync_complete_message import TxServiceSyncCompleteMessage
from bxcommon.messages.bloxroute.tx_service_sync_blocks_short_ids_message import TxServiceSyncBlocksShortIdsMessage
from bxcommon.messages.bloxroute.txs_serializer import TxContentShortIds
from bxcommon.messages.bloxroute.blocks_short_ids_serializer import BlockShortIds
from bxcommon.messages.bloxroute import txs_serializer
from bxcommon.utils import nonce_generator
from bxcommon.utils.buffers.output_buffer import OutputBuffer
from bxcommon.utils.expiring_dict import ExpiringDict
from bxcommon.utils.stats import hooks
from bxcommon.utils.stats.measurement_type import MeasurementType
from bxcommon.utils.object_hash import Sha256Hash

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

    def msg_tx_service_sync_txs(self, msg: TxServiceSyncTxsMessage):
        """
        Transaction service sync message receive txs data
        """
        network_num = msg.network_num()
        tx_service = self.node.get_tx_service(network_num)
        txs_content_short_ids = msg.txs_content_short_ids()

        for tx_content_short_ids in txs_content_short_ids:
            tx_hash = tx_content_short_ids.tx_hash
            tx_service.set_transaction_contents(tx_hash, tx_content_short_ids.tx_content)
            for short_id in tx_content_short_ids.short_ids:
                tx_service.assign_short_id(tx_hash, short_id)

    def _create_txs_service_msg(self, network_num: int, tx_service_snap: List[Sha256Hash]) -> List[TxContentShortIds]:
        txs_content_short_ids: List[TxContentShortIds] = []
        txs_msg_len = 0

        while tx_service_snap:
            tx_hash = tx_service_snap.pop()
            tx_content_short_ids = TxContentShortIds(
                tx_hash,
                self.node.get_tx_service(network_num).get_transaction_by_hash(tx_hash),
                self.node.get_tx_service(network_num).get_short_ids(tx_hash)
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
        self.enqueue_msg(TxServiceSyncReqMessage(network_num))

    def send_tx_service_sync_complete(self, network_num: int):
        self.enqueue_msg(TxServiceSyncCompleteMessage(network_num))

    def send_tx_service_sync_blocks_short_ids(self, network_num: int):
        blocks_short_ids: List[BlockShortIds] = []
        start_time = time.time()
        for block_hash, short_ids in self.node.get_tx_service(network_num).iter_short_ids_seen_in_block():
            blocks_short_ids.append(BlockShortIds(block_hash, short_ids))

        block_short_ids_msg = TxServiceSyncBlocksShortIdsMessage(network_num, blocks_short_ids)
        duration = time.time() - start_time
        logger.info("BlockShortIds in network {}, {} blocks took {} ms ".format(network_num, len(blocks_short_ids), duration))
        self.enqueue_msg(block_short_ids_msg)

    def send_tx_service_sync_txs(self, network_num: int, tx_service_snap: List[Sha256Hash], duration: float = 0, msgs_count: int = 0, total_tx_count: int = 0, sending_tx_msgs_start_time: float = 0):
        if (time.time() - sending_tx_msgs_start_time) < constants.SENDING_TX_MSGS_TIMEOUT_MS:
            if tx_service_snap:
                start = time.time()
                txs_content_short_ids = self._create_txs_service_msg(network_num, tx_service_snap)
                self.enqueue_msg(TxServiceSyncTxsMessage(network_num, txs_content_short_ids))
                duration += time.time() - start
                msgs_count += 1
                total_tx_count += len(txs_content_short_ids)
            if tx_service_snap:     # checks again if tx_snap in case we still have msgs to send, else no need to wait TX_SERVICE_SYNC_TXS_S seconds
                self.node.alarm_queue.register_alarm(
                    constants.TX_SERVICE_SYNC_TXS_S, self.send_tx_service_sync_txs, network_num, tx_service_snap, duration, msgs_count, total_tx_count, sending_tx_msgs_start_time
                )
            else:   # if all txs were sent, send complete msg
                logger.info(
                    "Sending TxServiceSyncTxsMessage in network {}, {} transactions and {} messages took {} ms ".
                    format(network_num, total_tx_count, msgs_count, duration * 1000))
                self.send_tx_service_sync_complete(network_num)
        else:   # if time is up - upgrade this node as synced - giving up
            logger.info("Sending TxServiceSyncTxsMessage in network {}, {} transactions and {} messages took more than {} ms ".
                        format(network_num, total_tx_count, msgs_count, constants.SENDING_TX_MSGS_TIMEOUT_MS))
            self.send_tx_service_sync_complete(network_num)

    def msg_tx_service_sync_complete(self, _msg: TxServiceSyncCompleteMessage):
        self.node.on_fully_updated_tx_service()
