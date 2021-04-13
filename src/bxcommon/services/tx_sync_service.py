import time
from typing import List, Optional, Set, Dict, Any, TYPE_CHECKING

from bxutils.logging import LogRecordType
from bxutils import logging

from bxcommon import constants
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.messages.bloxroute.blocks_short_ids_serializer import BlockShortIds
from bxcommon.messages.bloxroute.tx_service_sync_blocks_short_ids_message import TxServiceSyncBlocksShortIdsMessage
from bxcommon.messages.bloxroute.tx_service_sync_complete_message import TxServiceSyncCompleteMessage
from bxcommon.messages.bloxroute.tx_service_sync_req_message import TxServiceSyncReqMessage
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import TxServiceSyncTxsMessage
from bxcommon import log_messages
from bxcommon.models.node_type import NodeType
from bxcommon.services import tx_sync_service_helpers
from bxcommon.services.transaction_service import TransactionCacheKeyType
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.models.transaction_flag import TransactionFlag
from bxcommon.utils import performance_utils

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from bxcommon.connections.internal_node_connection import InternalNodeConnection

logger = logging.get_logger(__name__)
performance_troubleshooting_logger = logging.get_logger(
    LogRecordType.PerformanceTroubleshooting, __name__
)


class TxSyncService:
    def __init__(self, conn: "InternalNodeConnection") -> None:
        self.conn = conn
        self.node = conn.node
        self._sync_alarms: Dict[int, Any] = dict()

    def msg_tx_service_sync_txs(self, msg: TxServiceSyncTxsMessage) -> None:
        """
        Transaction service sync message receive txs data
        """

        network_num = msg.network_num()
        self.node.last_sync_message_received_by_network[network_num] = time.time()
        tx_service = self.node.get_tx_service(network_num)

        result_items = tx_service.process_tx_sync_message(msg)
        sync_metrics = self.node.sync_metrics[network_num]
        sync_metrics["msgs"] += 1
        for item in result_items:
            sync_metrics["tx_count"] += 1

            if item.content_length > 0:
                sync_metrics["tx_content_count"] += 1

            for short_id, transaction_flag in zip(
                item.short_ids, item.transaction_flag_types
            ):
                self.node.sync_short_id_buckets[network_num].incr_short_id(short_id)
                if TransactionFlag.PAID_TX in transaction_flag:
                    tx_service.set_short_id_transaction_type(short_id, transaction_flag)

        self.conn.log_debug(
            "TxSync processed msg from {} network {}, msgs: {}, transactions: {}, content: {}",
            self.conn,
            network_num,
            sync_metrics["msgs"],
            sync_metrics["tx_count"],
            sync_metrics["tx_content_count"],
        )

    def send_tx_service_sync_req(self, network_num: int):
        """
        sending transaction service sync request
        """
        self.node.last_sync_message_received_by_network[network_num] = time.time()
        self.node.sync_short_id_buckets.pop(network_num, None)
        self.node.sync_metrics.pop(network_num, None)
        self.conn.enqueue_msg(TxServiceSyncReqMessage(network_num))

        if self.node.check_sync_relay_connections_alarm_id:
            self.node.alarm_queue.unregister_alarm(self.node.check_sync_relay_connections_alarm_id)
            self.node.check_sync_relay_connections_alarm_id = None
        self.node.check_sync_relay_connections_alarm_id = self.node.alarm_queue.register_alarm(
            constants.LAST_MSG_FROM_RELAY_THRESHOLD_S, self.node.check_sync_relay_connections, self.conn
        )

    def send_tx_service_sync_complete(self, network_num: int) -> None:
        self.conn.update_tx_sync_complete(network_num)
        self.conn.enqueue_msg(TxServiceSyncCompleteMessage(network_num))

    def send_tx_service_sync_blocks_short_ids(self, network_num: int) -> None:
        blocks_short_ids: List[BlockShortIds] = []
        start_time = time.time()
        for block_hash, short_ids in self.node.get_tx_service(
            network_num
        ).iter_short_ids_seen_in_block():
            blocks_short_ids.append(BlockShortIds(block_hash, short_ids))

        block_short_ids_msg = TxServiceSyncBlocksShortIdsMessage(
            network_num, blocks_short_ids
        )
        performance_utils.log_operation_duration(
            performance_troubleshooting_logger,
            "Create tx service sync block short ids message",
            start_time,
            constants.RESPONSIVENESS_CHECK_DELAY_WARN_THRESHOLD_S,
            network_num=network_num,
            connection=self.conn,
            blocks_short_ids_count=len(blocks_short_ids),
        )
        duration = time.time() - start_time
        self.conn.log_trace(
            "Sending {} block short ids took {:.3f} seconds.",
            len(blocks_short_ids),
            duration,
        )
        self.conn.enqueue_msg(block_short_ids_msg)

    def send_tx_service_sync_txs(
        self,
        network_num: int,
        tx_service_snap: List[Sha256Hash],
        sync_tx_content: bool = True,
        duration: float = 0,
        msgs_count: int = 0,
        total_tx_count: int = 0,
        sending_tx_msgs_start_time: float = 0,
    ) -> None:
        if network_num in self._sync_alarms:
            del self._sync_alarms[network_num]

        if not self.conn.is_active():
            self.conn.log_info(
                "TxSync on network {}, sent {} transactions, and {} messages, took {:.3f}s. "
                "{} transactions were not synced. Connection had been closed",
                network_num,
                total_tx_count,
                msgs_count,
                duration,
                len(tx_service_snap),
            )
            self.send_tx_service_sync_complete(network_num)
            return

        if sending_tx_msgs_start_time == 0:
            sending_tx_msgs_start_time = time.time()
        tx_service = self.node.get_tx_service(network_num)
        sync_ping_latency = self.conn.sync_ping_latencies.get(network_num, 0.0)
        if (
            time.time() - sending_tx_msgs_start_time
        ) < constants.SENDING_TX_MSGS_TIMEOUT_S:
            if tx_service_snap and sync_ping_latency is not None:
                start = time.time()
                txs_content_short_ids = tx_sync_service_helpers.create_txs_service_msg(
                    tx_service, tx_service_snap, sync_tx_content
                )
                performance_utils.log_operation_duration(
                    performance_troubleshooting_logger,
                    "Create tx service sync message",
                    start,
                    constants.RESPONSIVENESS_CHECK_DELAY_WARN_THRESHOLD_S,
                    network_num=network_num,
                    connection=self,
                    tx_count=len(txs_content_short_ids),
                )
                self.conn.enqueue_msg(
                    TxServiceSyncTxsMessage(network_num, txs_content_short_ids)
                )
                self.conn.check_ping_latency_for_network(network_num)
                duration += time.time() - start
                msgs_count += 1
                total_tx_count += len(txs_content_short_ids)
            # checks again if tx_snap in case we still have msgs to send, else no need to wait
            # for the next interval.
            if tx_service_snap:
                if sync_ping_latency is None:
                    next_interval = constants.TX_SERVICE_SYNC_TXS_S
                else:
                    next_interval = max(
                        sync_ping_latency * 0.5, constants.TX_SERVICE_SYNC_TXS_S
                    )
                self._sync_alarms[network_num] = self.node.alarm_queue.register_alarm(
                    next_interval,
                    self.send_tx_service_sync_txs,
                    network_num,
                    tx_service_snap,
                    sync_tx_content,
                    duration,
                    msgs_count,
                    total_tx_count,
                    sending_tx_msgs_start_time,
                )
            else:  # if all txs were sent, send complete msg
                self.conn.log_debug(
                    "TxSync on network {}, sent {} transactions, and {} messages, took {:.3f}s.",
                    network_num,
                    total_tx_count,
                    msgs_count,
                    duration,
                )
                self.send_tx_service_sync_complete(network_num)
        else:  # if time is up - upgrade this node as synced - giving up
            self.conn.log_debug(
                "TxSync on network {}, sent {} transactions, and {} messages, took more than {}s. Giving up. "
                "{} transactions were not synced",
                network_num,
                total_tx_count,
                msgs_count,
                constants.SENDING_TX_MSGS_TIMEOUT_S,
                len(tx_service_snap),
            )
            self.send_tx_service_sync_complete(network_num)

    def send_tx_service_sync_txs_from_time(
        self,
        network_num: int,
        sync_tx_content: bool = True,
        duration: float = 0,
        msgs_count: int = 0,
        total_tx_count: int = 0,
        sending_tx_msgs_start_time: float = 0,
        start_time: float = 0,
        snapshot_cache_keys: Optional[Set[TransactionCacheKeyType]] = None,
    ) -> None:
        if network_num in self._sync_alarms:
            del self._sync_alarms[network_num]

        if not self.conn.is_active():
            self.conn.log_info(
                "TxSync on network {}, sent {} transactions, and {} messages, took {:.3f}s. "
                "Connection had been closed",
                self,
                network_num,
                total_tx_count,
                msgs_count,
                duration,
            )
            self.send_tx_service_sync_complete(network_num)
            return

        if sending_tx_msgs_start_time == 0:
            sending_tx_msgs_start_time = time.time()
        done = False
        last_tx_timestamp = start_time
        sync_ping_latency = self.conn.sync_ping_latencies.get(network_num, 0.0)
        tx_service = self.node.get_tx_service(network_num)
        if (
            time.time() - sending_tx_msgs_start_time
        ) < constants.SENDING_TX_MSGS_TIMEOUT_S:
            if sync_ping_latency is not None:
                start = time.time()
                (
                    txs_content_short_ids,
                    last_tx_timestamp,
                    done,
                    snapshot_cache_keys,
                ) = tx_sync_service_helpers.create_txs_service_msg_from_time(
                    tx_service, start_time, sync_tx_content, snapshot_cache_keys
                )
                self.conn.log_info(
                    "TxSync on network {}, syncing {} transactions created between {} and {} start {} end {}, "
                    "took {:.3f}s. {} transactions were synced.",
                    network_num,
                    len(snapshot_cache_keys),
                    start_time,
                    last_tx_timestamp,
                    time.time() - start,
                    "All" if done else "Not all",
                )
                performance_utils.log_operation_duration(
                    performance_troubleshooting_logger,
                    "Create tx service sync message from time",
                    start,
                    constants.RESPONSIVENESS_CHECK_DELAY_WARN_THRESHOLD_S,
                    network_num=network_num,
                    connection=self,
                    tx_count=len(txs_content_short_ids),
                )
                self.conn.enqueue_msg(
                    TxServiceSyncTxsMessage(network_num, txs_content_short_ids)
                )
                self.conn.check_ping_latency_for_network(network_num)
                duration += time.time() - start
                msgs_count += 1
                total_tx_count += len(txs_content_short_ids)
            # checks again if tx_snap in case we still have msgs to send, else no need to wait
            # for the next interval.
            if not done:
                if sync_ping_latency is None:
                    next_interval = constants.TX_SERVICE_SYNC_TXS_S
                else:
                    next_interval = max(
                        sync_ping_latency * 0.5, constants.TX_SERVICE_SYNC_TXS_S
                    )
                self._sync_alarms[network_num] = self.node.alarm_queue.register_alarm(
                    next_interval,
                    self.send_tx_service_sync_txs_from_time,
                    network_num,
                    sync_tx_content,
                    duration,
                    msgs_count,
                    total_tx_count,
                    sending_tx_msgs_start_time,
                    last_tx_timestamp,
                    snapshot_cache_keys,
                )
            else:  # if all txs were sent, send complete msg
                self.conn.log_info(
                    "TxSync on network {}, sent {} transactions, and {} messages, took {:.3f}s.",
                    network_num,
                    total_tx_count,
                    msgs_count,
                    duration,
                )
                self.send_tx_service_sync_complete(network_num)
        else:  # if time is up - upgrade this node as synced - giving up
            self.conn.log_info(
                "TxSync on network {}, sent {} transactions, and {} messages, took more than {:.3f}s. Giving up. "
                "{} transactions since were not synced",
                network_num,
                total_tx_count,
                msgs_count,
                constants.SENDING_TX_MSGS_TIMEOUT_S,
                last_tx_timestamp,
            )
            self.send_tx_service_sync_complete(network_num)

    def send_tx_service_sync_txs_from_buffer(
        self,
        network_num: int,
        txs_buffer: memoryview,
        duration: float = 0,
        msgs_count: int = 0,
        total_tx_count: int = 0,
        sending_tx_msgs_start_time: float = 0,
        start_offset: int = 0,
    ) -> None:
        if network_num in self._sync_alarms:
            del self._sync_alarms[network_num]
        if not self.conn:
            logger.warning(log_messages.CONNECTION_DOES_NOT_EXIST, "sync alarm (send_tx_service_sync_txs_from_buffer)")
            return
        if not self.conn.is_active():
            self.conn.log_info(
                "TxSync on network {}, sent {} transactions, and {} messages, took {:.3f}s. "
                "Connection had been closed",
                network_num,
                total_tx_count,
                msgs_count,
                duration,
            )
            self.send_tx_service_sync_complete(network_num)
            return

        if sending_tx_msgs_start_time == 0:
            sending_tx_msgs_start_time = time.time()

        done = False
        end_offset = start_offset

        sync_ping_latency = self.conn.sync_ping_latencies.get(network_num, 0.0)
        tx_service = self.node.get_tx_service(network_num)
        if (
            time.time() - sending_tx_msgs_start_time
        ) < constants.SENDING_TX_MSGS_TIMEOUT_S:
            if sync_ping_latency is not None:
                start = time.time()

                (
                    txs_msg,
                    txs_count,
                    end_offset,
                    done,
                ) = tx_sync_service_helpers.create_txs_service_msg_from_buffer(
                    tx_service, txs_buffer, start_offset
                )
                self.conn.log_info(
                    "TxSync on network {}, syncing {} transactions, took {:.3f}s. "
                    "Starting offset {}, ending offset {}, total offset {}. "
                    "{} transactions were synced.",
                    network_num,
                    txs_count,
                    time.time() - start,
                    start_offset,
                    end_offset,
                    len(txs_buffer),
                    "All" if done else "Not all",
                )
                performance_utils.log_operation_duration(
                    performance_troubleshooting_logger,
                    "Create tx service sync message from time",
                    start,
                    constants.RESPONSIVENESS_CHECK_DELAY_WARN_THRESHOLD_S,
                    network_num=network_num,
                    connection=self,
                    tx_count=txs_count,
                )
                self.conn.enqueue_msg(txs_msg)
                self.conn.check_ping_latency_for_network(network_num)
                duration += time.time() - start
                msgs_count += 1
                total_tx_count += txs_count

            # checks again if tx_snap in case we still have msgs to send, else no need to wait
            # for the next interval.
            if not done:
                if sync_ping_latency is None:
                    next_interval = constants.TX_SERVICE_SYNC_TXS_S
                else:
                    next_interval = max(
                        sync_ping_latency * 0.5, constants.TX_SERVICE_SYNC_TXS_S
                    )
                self._sync_alarms[network_num] = self.node.alarm_queue.register_alarm(
                    next_interval,
                    self.send_tx_service_sync_txs_from_buffer,
                    network_num,
                    txs_buffer,
                    duration,
                    msgs_count,
                    total_tx_count,
                    sending_tx_msgs_start_time,
                    end_offset,
                )
            else:  # if all txs were sent, send complete msg
                self.conn.log_info(
                    "TxSync on network {}, sent {} transactions, and {} messages. took {:.3f}s.",
                    network_num,
                    total_tx_count,
                    msgs_count,
                    duration,
                )
                self.send_tx_service_sync_complete(network_num)
        else:  # if time is up - upgrade this node as synced - giving up
            self.conn.log_info(
                "TxSync on network {}, sent {} transactions, and {} messages, took more than {:.3f}s. Giving up. "
                "{} bytes out of {} total were synced",
                network_num,
                total_tx_count,
                msgs_count,
                constants.SENDING_TX_MSGS_TIMEOUT_S,
                start_offset,
                len(txs_buffer),
            )
            self.send_tx_service_sync_complete(network_num)

    def msg_tx_service_sync_complete(self, msg: TxServiceSyncCompleteMessage) -> None:
        if (
            self.node.NODE_TYPE in NodeType.GATEWAY
            # pylint: disable=unsupported-membership-test
            and ConnectionType.RELAY_BLOCK == self.conn.CONNECTION_TYPE
        ):
            return
        if self.node.check_sync_relay_connections_alarm_id:
            self.node.alarm_queue.unregister_alarm(self.node.check_sync_relay_connections_alarm_id)
            self.node.check_sync_relay_connections_alarm_id = None
        if self.node.transaction_sync_timeout_alarm_id:
            self.node.alarm_queue.unregister_alarm(self.node.transaction_sync_timeout_alarm_id)
            self.node.transaction_sync_timeout_alarm_id = None
        network_num = msg.network_num()
        self.node.on_network_synced(network_num)
        duration = time.time() - self.node.start_sync_time
        self.conn.log_info(
            "TxSync complete. It took {:.3f} seconds to complete transaction state with BDN.",
            duration,
        )
        sync_data: Dict[str, Any] = {"peer_id": self.conn.peer_id, "duration": duration}
        for network_num, sync_metrics in self.node.sync_metrics.items():
            tx_service = self.node.get_tx_service(network_num)
            network_stats = dict(sync_metrics)
            network_stats["content_without_sid"] = len(
                tx_service.tx_hashes_without_short_id.queue
            )
            network_stats["sid_without_content"] = len(
                tx_service.tx_hashes_without_content.queue
            )
            # pylint: disable=protected-access
            # noinspection PyProtectedMember
            network_stats["tx_content_len"] = len(tx_service._tx_cache_key_to_contents)
            sync_data[network_num] = network_stats

        sync_data["short_id_buckets"] = self.node.sync_short_id_buckets

        logger.debug({"type": "TxSyncMetrics", "data": sync_data})
        self.node.on_fully_updated_tx_service()

    def dispose(self):
        self.conn = None
