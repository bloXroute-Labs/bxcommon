import struct
from typing import Optional, List, TYPE_CHECKING

from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType

from bxcommon import constants
from bxcommon.constants import BX_HDR_COMMON_OFF
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.models.broadcast_message_type import BroadcastMessageType
from bxcommon.utils import crypto, convert
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.utils.stats.statistics_event_service import StatisticsEventService

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from bxcommon.connections.abstract_connection import AbstractConnection


class _BlockStatisticsService(StatisticsEventService):
    BROADCAST_TYPE_OFFSET = BX_HDR_COMMON_OFF + crypto.SHA256_HASH_LEN + \
                            constants.NETWORK_NUM_LEN + constants.NODE_ID_SIZE_IN_BYTES

    def __init__(self) -> None:
        super(_BlockStatisticsService, self).__init__()
        self.name = "BlockInfo"
        self.logger = logging.get_logger(LogRecordType.BlockInfo)
        self.priority_logger = logging.get_logger(LogRecordType.BlockPropagationInfo)
        self.log_detailed_block_stats = False

    def set_node(self, node) -> None:
        super(_BlockStatisticsService, self).set_node(node)
        assert node.opts is not None
        self.log_detailed_block_stats = node.opts.log_detailed_block_stats

    def add_block_event(
        self,
        block_msg,
        block_event_settings,
        network_num,
        start_date_time=None,
        end_date_time=None,
        peers: Optional[List["AbstractConnection"]] = None,
        **kwargs
    ) -> None:
        if not self._should_log_stat_event(block_event_settings):
            return

        if isinstance(block_msg, BroadcastMessage):
            block_hash = block_msg.block_hash().binary
            broadcast_type = block_msg.broadcast_type().value
        elif isinstance(block_msg, memoryview):
            block_hash = block_msg[BX_HDR_COMMON_OFF:BX_HDR_COMMON_OFF + crypto.SHA256_HASH_LEN].tobytes()
            broadcast_type = struct.unpack_from(
                "<4s", block_msg[self.BROADCAST_TYPE_OFFSET:
                                 self.BROADCAST_TYPE_OFFSET + constants.BROADCAST_TYPE_LEN].tobytes()
            )[0].decode(constants.DEFAULT_TEXT_ENCODING)
        else:
            block_hash = block_msg[BX_HDR_COMMON_OFF:BX_HDR_COMMON_OFF + crypto.SHA256_HASH_LEN]
            broadcast_type = struct.unpack_from(
                "<4s", block_msg[self.BROADCAST_TYPE_OFFSET:self.BROADCAST_TYPE_OFFSET + constants.BROADCAST_TYPE_LEN]
            )[0].decode(constants.DEFAULT_TEXT_ENCODING)

        self.log_event(
            block_event_settings, convert.bytes_to_hex(block_hash), start_date_time, end_date_time,
            network_num=network_num, broadcast_type=broadcast_type, peers=peers, **kwargs
        )

    def add_block_event_by_block_hash(
        self,
        block_hash,
        block_event_settings,
        network_num,
        broadcast_type=BroadcastMessageType.BLOCK,
        start_date_time=None,
        end_date_time=None,
        peers: Optional[List["AbstractConnection"]] = None,
        **kwargs
    ) -> None:
        if not self._should_log_stat_event(block_event_settings):
            return

        if isinstance(block_hash, Sha256Hash):
            block_hash_str = block_hash.binary
        elif isinstance(block_hash, memoryview):
            block_hash_str = block_hash.tobytes()
        else:
            block_hash_str = block_hash

        self.log_event(
            block_event_settings,
            convert.bytes_to_hex(block_hash_str),
            start_date_time,
            end_date_time,
            network_num=network_num,
            broadcast_type=broadcast_type.value,
            peers=peers, **kwargs)

    def _should_log_stat_event(self, event_type_settings) -> bool:
        return self.log_detailed_block_stats or not event_type_settings.detailed_stat_event


block_stats = _BlockStatisticsService()
