from bxcommon.constants import BX_HDR_COMMON_OFF
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.utils import crypto, convert
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.utils.stats.statistics_event_service import StatisticsEventService
from bxutils.logging.log_record_type import LogRecordType
from bxutils import logging


class _BlockStatisticsService(StatisticsEventService):
    def __init__(self):
        super(_BlockStatisticsService, self).__init__()
        self.name = "BlockInfo"
        self.logger = logging.get_logger(LogRecordType.BlockInfo, __name__)

    def add_block_event(self, block_msg, block_event_settings, network_num, start_date_time=None, end_date_time=None,
                        **kwargs):
        if not self._should_log_stat_event(block_event_settings):
            return

        if isinstance(block_msg, BroadcastMessage):
            block_hash = block_msg.block_hash().binary
        elif isinstance(block_msg, memoryview):
            block_hash = block_msg[BX_HDR_COMMON_OFF:BX_HDR_COMMON_OFF + crypto.SHA256_HASH_LEN].tobytes()
        else:
            block_hash = block_msg[BX_HDR_COMMON_OFF:BX_HDR_COMMON_OFF + crypto.SHA256_HASH_LEN]

        self.log_event(block_event_settings, convert.bytes_to_hex(block_hash), start_date_time, end_date_time,
                       network_num=network_num,
                       **kwargs)

    def add_block_event_by_block_hash(self, block_hash, block_event_settings, network_num, start_date_time=None, end_date_time=None,
                                      **kwargs):
        if not self._should_log_stat_event(block_event_settings):
            return

        if isinstance(block_hash, Sha256Hash):
            block_hash_str = block_hash.binary
        elif isinstance(block_hash, memoryview):
            block_hash_str = block_hash.tobytes()
        else:
            block_hash_str = block_hash

        self.log_event(block_event_settings, convert.bytes_to_hex(block_hash_str), start_date_time, end_date_time,
                       network_num=network_num,
                       **kwargs)

    def _should_log_stat_event(self, event_type_settings):
        return self.node.opts.log_detailed_block_stats or not event_type_settings.detailed_stat_event


block_stats = _BlockStatisticsService()
