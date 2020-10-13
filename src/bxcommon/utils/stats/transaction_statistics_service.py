import datetime
import struct
from collections import defaultdict
from typing import Optional, Dict, List, TYPE_CHECKING

from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType

from bxcommon import constants
from bxcommon.utils import convert
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.utils.stats.stat_event_type_settings import StatEventTypeSettings
from bxcommon.utils.stats.statistics_event_service import StatisticsEventService

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from bxcommon.connections.abstract_connection import AbstractConnection

logger = logging.get_logger(__name__)


class _TransactionStatisticsService(StatisticsEventService):
    def __init__(self) -> None:
        super(_TransactionStatisticsService, self).__init__()
        self.name = "TransactionInfo"
        self.logger = logging.get_logger(LogRecordType.TransactionInfo)
        self.priority_logger = logging.get_logger(LogRecordType.TransactionPropagationInfo)

        self.log_percentage_for_hash_by_network_num: Dict[int, float] = \
            defaultdict(lambda: constants.TRANSACTIONS_BY_HASH_PERCENTAGE_TO_LOG_STATS_FOR)
        self.log_percentage_for_sid_by_network_num: Dict[int, float] = \
            defaultdict(lambda: constants.TRANSACTIONS_BY_SID_PERCENTAGE_TO_LOG_STATS_FOR)

    def configure_network(self, network_num: int, percent_to_log_by_hash: float, percent_to_log_by_sid: float) -> None:
        self.log_percentage_for_hash_by_network_num[network_num] = percent_to_log_by_hash
        self.log_percentage_for_sid_by_network_num[network_num] = percent_to_log_by_sid

    def add_tx_by_hash_event(
        self,
        tx_hash: Sha256Hash,
        tx_event_settings: StatEventTypeSettings,
        network_num: int,
        short_id: Optional[int] = None,
        start_date_time: Optional[datetime.datetime] = None,
        end_date_time: Optional[datetime.datetime] = None,
        peers: Optional[List["AbstractConnection"]] = None,
        **kwargs
    ) -> None:
        tx_hash = tx_hash.binary
        if self.should_log_event_for_tx(tx_hash, network_num, short_id):
            self.log_event(tx_event_settings, convert.bytes_to_hex(tx_hash), start_date_time, end_date_time,
                           short_id=short_id, network_num=network_num, peers=peers, **kwargs)

    def add_txs_by_short_ids_event(
        self,
        short_ids,
        tx_event_settings: StatEventTypeSettings,
        network_num: int,
        start_date_time: Optional[datetime.datetime] = None,
        end_date_time: Optional[datetime.datetime] = None,
        peers: Optional[List["AbstractConnection"]] = None,
        **kwargs
    ) -> None:
        if not constants.ENABLE_TRANSACTIONS_STATS_BY_SHORT_IDS:
            return

        if len(short_ids) < 1:
            # TODO: should be an assertion
            logger.debug("Attempted to log message with 0 short ids!")
            return

        if not tx_event_settings:
            raise ValueError("tx_event_name is required")

        if self.log_percentage_for_hash_by_network_num[network_num] >= 0:
            self.log_event(
                tx_event_settings, short_ids, start_date_time, end_date_time,
                network_num=network_num, peers=peers, **kwargs
            )

    def should_log_event_for_tx(
        self, tx_hash_bytes: bytearray, network_num: int, short_id: Optional[int]
    ) -> bool:
        percent_to_log_by_tx_hash = self.log_percentage_for_hash_by_network_num[network_num]
        percent_to_log_by_sid = self.log_percentage_for_sid_by_network_num[network_num]
        if percent_to_log_by_tx_hash <= 0 and percent_to_log_by_sid <= 0:
            return False

        last_byte_value, = struct.unpack_from("<B", tx_hash_bytes, len(tx_hash_bytes) - 1)
        log_tx_stat_probability_value = float(last_byte_value) * 100 / constants.MAX_BYTE_VALUE
        should_log_tx_hash = log_tx_stat_probability_value <= percent_to_log_by_tx_hash

        should_log_short_id = False
        # exclude short_id == 0 as well
        if short_id:
            should_log_short_id = float(short_id % 10000 + 1) / 100 <= percent_to_log_by_sid

        return should_log_tx_hash or should_log_short_id


tx_stats = _TransactionStatisticsService()
