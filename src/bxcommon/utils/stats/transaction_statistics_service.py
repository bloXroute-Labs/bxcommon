import struct

from bxcommon import constants
from bxcommon.utils import convert, logger
from bxcommon.utils.object_hash import ObjectHash
from bxcommon.utils.stats.statistics_event_service import StatisticsEventService


class _TransactionStatisticsService(StatisticsEventService):
    def __init__(self):
        super(_TransactionStatisticsService, self).__init__()
        self.name = "TransactionInfo"

    def add_tx_by_hash_event(self, tx_hash, tx_event_name, start_date_time=None, end_date_time=None, **kwargs):
        if not tx_hash:
            raise ValueError("tx_hash is required")

        if not tx_event_name:
            raise ValueError("tx_event_name is required")

        if isinstance(tx_hash, ObjectHash):
            tx_hash = tx_hash.binary

        if self._should_log_event_for_tx(tx_hash):
            self.log_event(tx_event_name, convert.bytes_to_hex(tx_hash), start_date_time, end_date_time, **kwargs)

    def add_txs_by_short_ids_event(self, short_ids, tx_event_name, start_date_time=None, end_date_time=None, **kwargs):
        if not constants.ENABLE_TRANSACTIONS_STATS_BY_SHORT_IDS:
            return

        if len(short_ids) < 1:
            logger.warn("Attempted to log message with 0 short ids!")
            return

        if not tx_event_name:
            raise ValueError("tx_event_name is required")

        if constants.TRANSACTIONS_PERCENTAGE_TO_LOG_STATS_FOR >= 0:
             self.log_event(tx_event_name, short_ids, start_date_time, end_date_time, **kwargs)

    def _should_log_event_for_tx(self, tx_hash_bytes):
        if constants.TRANSACTIONS_PERCENTAGE_TO_LOG_STATS_FOR <= 0:
            return False

        last_byte_value, = struct.unpack_from("<B", tx_hash_bytes, len(tx_hash_bytes) - 1)

        log_tx_stat_probability_value = float(last_byte_value) * 100 / constants.MAX_BYTE_VALUE

        return log_tx_stat_probability_value <= constants.TRANSACTIONS_PERCENTAGE_TO_LOG_STATS_FOR


tx_stats = _TransactionStatisticsService()
