import datetime

from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.utils import crypto, convert, publish_stats
from bxcommon.utils.object_hash import ObjectHash
from bxcommon.utils.stats.stat_event import StatEvent


class _BlockStatisticsService(object):
    def __init__(self):
        self.name = "BlockInfo"

    def add_block_event(self, block_msg, block_event_name, start_date_time=None, end_date_time=None,
                        **kwargs):
        if isinstance(block_msg, BroadcastMessage):
            block_hash = block_msg.msg_hash().binary
        elif isinstance(block_msg, memoryview):
            block_hash = block_msg[HDR_COMMON_OFF:HDR_COMMON_OFF + crypto.SHA256_HASH_LEN].tobytes()
        else:
            block_hash = block_msg[HDR_COMMON_OFF:HDR_COMMON_OFF + crypto.SHA256_HASH_LEN]

        self._log_event(block_event_name, block_hash, start_date_time, end_date_time, **kwargs)

    def add_block_event_by_block_hash(self, block_hash, block_event_name, start_date_time=None, end_date_time=None,
                                      **kwargs):
        if isinstance(block_hash, ObjectHash):
            block_hash_str = block_hash.binary
        elif isinstance(block_hash, memoryview):
            block_hash_str = block_hash.tobytes()
        else:
            block_hash_str = block_hash

        self._log_event(block_event_name, block_hash_str, start_date_time, end_date_time, **kwargs)

    def _log_event(self, event_name, block_hash, start_date_time=None, end_date_time=None, **kwargs):

        if start_date_time is None:
            start_date_time = datetime.datetime.utcnow()

        if end_date_time is None:
            end_date_time = start_date_time

        stat_event = StatEvent(event_name, convert.bytes_to_hex(block_hash), start_date_time, end_date_time, **kwargs)
        publish_stats.publish_stats(self.name, stat_event)


block_stats = _BlockStatisticsService()
