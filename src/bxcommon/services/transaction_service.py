# pylint: disable=too-many-lines

import functools
import time
import typing
from collections import defaultdict, OrderedDict, Counter
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import reduce
from typing import List, Tuple, Generator, Optional, Union, Dict, Set, Any, Iterator, TYPE_CHECKING

from prometheus_client import Gauge

from bxcommon import constants
from bxcommon.messages.bloxroute import short_ids_serializer
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import TxServiceSyncTxsMessage
from bxcommon.models.transaction_flag import TransactionFlag
from bxcommon.models.transaction_info import TransactionSearchResult, TransactionInfo
from bxcommon.models.transaction_key import TransactionKey, TransactionCacheKeyType
from bxcommon.utils import memory_utils, convert
from bxcommon.utils.crypto import SHA256_HASH_LEN
from bxcommon.utils.deprecated import deprecated
from bxcommon.utils.expiration_queue import ExpirationQueue
from bxcommon.utils.memory_utils import ObjectSize, SizeType
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.utils.stats import hooks
from bxcommon.utils.stats.transaction_stat_event_type import TransactionStatEventType
from bxcommon.utils.stats.transaction_statistics_service import tx_stats
from bxutils import log_messages
from bxutils import logging, utils
from bxutils.encoding import json_encoder
from bxutils.logging.log_record_type import LogRecordType

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode
else:
    tpe_Sha256 = Any

logger = logging.get_logger(__name__)
logger_memory_cleanup = logging.get_logger(LogRecordType.BlockCleanup, __name__)
logger_tx_histogram = logging.get_logger(LogRecordType.TransactionHistogram, __name__)
performance_logger = logging.get_logger(LogRecordType.PerformanceTroubleshooting, __name__)

total_cached_transactions = Gauge(
    "cached_transaction_total",
    "Number of cached transactions",
    ("network",)
)
total_cached_transactions_size = Gauge(
    "cached_transaction_bytes",
    "Size of cached transactions",
    ("network",)
)


def wrap_sha256(transaction_hash: Union[bytes, bytearray, memoryview, Sha256Hash]) -> Sha256Hash:
    if isinstance(transaction_hash, Sha256Hash):
        return transaction_hash

    # pyre-fixme[25]: Assertion will always fail.
    if isinstance(transaction_hash, (bytes, bytearray, memoryview)):
        return Sha256Hash(binary=transaction_hash)

    return Sha256Hash(binary=convert.hex_to_bytes(transaction_hash))


class TxRemovalReason(Enum):
    UNKNOWN = "Unknown"
    BLOCK_CLEANUP = "BlockCleanup"
    EXTENSION_BLOCK_CLEANUP = "ExtensionBlockCleanup"
    MEMORY_LIMIT = "MemoryLimit"
    EXPIRATION = "Expiration"
    MEMPOOL_SYNC = "MempoolSync"


@dataclass
class TransactionServiceStats:
    short_id_count: int = 0
    transaction_content_count: int = 0
    transactions_removed_by_memory_limit: int = 0
    transaction_contents_size: int = 0

    def __sub__(self, other) -> "TransactionServiceStats":
        if not isinstance(other, TransactionServiceStats):
            raise TypeError(f"Cannot subtract object of type {type(other)} from TransactionServiceStats.")

        return TransactionServiceStats(
            self.short_id_count - other.short_id_count,
            self.transaction_content_count - other.transaction_content_count,
            self.transactions_removed_by_memory_limit - other.transactions_removed_by_memory_limit,
            self.transaction_contents_size - other.transaction_contents_size
        )


class TransactionFromBdnGatewayProcessingResult(typing.NamedTuple):
    ignore_seen: bool = False
    existing_short_id: bool = False
    assigned_short_id: bool = False
    existing_contents: bool = False
    set_content: bool = False


class TxSyncMsgProcessingItem(typing.NamedTuple):
    hash: Optional[Sha256Hash] = None
    content_length: int = 0
    short_ids: List[int] = []
    transaction_flag_types: List[TransactionFlag] = []


# pylint: disable=too-many-public-methods
class TransactionService:
    """
    Service for managing transaction mappings.
    In this class, we assume that no more than MAX_ID unassigned transactions exist at a time.

    Constants
    ---------
    MAX_ID: maximum short id value (e.g. number of bits in a short id)
    SHORT_ID_SIZE: number of bytes in a short id, must match TxMessage


    Attributes
    ----------
    node: reference to node holding transaction service reference
    tx_assign_alarm_scheduled: if an alarm to expire a batch of short ids is currently active
    network_num: network number that current transaction service serves
    _tx_cache_key_to_short_ids: mapping of transaction long hashes to (potentially multiple) short ids
    _short_id_to_tx_cache_key: mapping of short id to transaction long hashes
    _short_id_to_tx_flag: mapping of short id to transaction flag type
    _tx_cache_key_to_contents: mapping of transaction long hashes to transaction contents
    _tx_assignment_expire_queue: expiration time of short ids
    """

    node: "AbstractNode"
    tx_assign_alarm_scheduled: bool
    tx_content_without_sid_alarm_scheduled: bool
    network_num: int
    _short_id_to_tx_cache_key: Dict[int, TransactionCacheKeyType]
    _short_id_to_tx_flag: Dict[int, TransactionFlag]
    _tx_cache_key_to_contents: Dict[TransactionCacheKeyType, Union[bytearray, memoryview]]
    _tx_cache_key_to_short_ids: Dict[TransactionCacheKeyType, Set[int]]
    _tx_assignment_expire_queue: ExpirationQueue[int]
    _tx_hash_to_time_removed: OrderedDict
    _short_id_to_time_removed: OrderedDict
    tx_hashes_without_short_id: ExpirationQueue[Sha256Hash]
    tx_hashes_without_content: ExpirationQueue[Sha256Hash]  # but has short ID

    MAX_ID = 2 ** 32
    SHORT_ID_SIZE = 4
    DEFAULT_FINAL_TX_CONFIRMATIONS_COUNT = 24

    ESTIMATED_TX_HASH_AND_SHORT_ID_ITEM_SIZE = 376
    ESTIMATED_TX_HASH_ITEM_SIZE = 312
    ESTIMATED_SHORT_ID_EXPIRATION_ITEM_SIZE = 88
    ESTIMATED_TX_HASH_NOT_SEEN_IN_BLOCK_ITEM_SIZE = 312

    def __init__(self, node: "AbstractNode", network_num: int) -> None:
        """
        Constructor
        :param node: reference to node object
        :param network_num: network number
        """
        if node is None:
            raise ValueError("Node is required")

        if network_num is None:
            raise ValueError("Network number is required")

        self.node = node
        self.network_num = network_num

        self.tx_assign_alarm_scheduled = False
        self.tx_content_without_sid_alarm_scheduled = False
        self.tx_without_content_alarm_scheduled = False

        self._tx_cache_key_to_short_ids = defaultdict(set)
        self._short_id_to_tx_flag = {}
        self._short_id_to_tx_cache_key = {}
        self._tx_cache_key_to_contents = {}
        self._tx_assignment_expire_queue = ExpirationQueue(node.opts.sid_expire_time)
        self.tx_hashes_without_short_id = ExpirationQueue(constants.TX_CONTENT_NO_SID_EXPIRE_S)
        self.tx_hashes_without_content = ExpirationQueue(constants.TX_CONTENT_NO_SID_EXPIRE_S)
        self.network = None
        if self.network_num in self.node.opts.blockchain_networks:
            self.network = self.node.opts.blockchain_networks[self.network_num]

        self._tx_hash_to_time_removed = OrderedDict()
        self._short_id_to_time_removed = OrderedDict()

        self._final_tx_confirmations_count = self._get_final_tx_confirmations_count()
        self._tx_content_memory_limit = self._get_tx_contents_memory_limit()
        logger.debug("Memory limit for transaction service by network number {} is {} bytes.",
                     self.network_num, self._tx_content_memory_limit)
        self._removed_txs_expiration_time_s = self._get_removed_transactions_history_expiration_time_s()

        # short ids seen in block ordered by them block hash
        self._short_ids_seen_in_block: Dict[Sha256Hash, List[int]] = OrderedDict()
        self._total_tx_contents_size = 0
        self._total_tx_removed_by_memory_limit = 0

        self._last_transaction_stats = TransactionServiceStats()
        self._removed_short_ids = set()
        if node.opts.dump_removed_short_ids:
            self.node.alarm_queue.register_alarm(
                constants.DUMP_REMOVED_SHORT_IDS_INTERVAL_S,
                self._dump_removed_short_ids
            )
        self.node.alarm_queue.register_alarm(
            constants.REMOVED_TRANSACTIONS_HISTORY_CLEANUP_INTERVAL_S,
            self._cleanup_removed_transactions_history
        )

        self.total_cached_transactions = total_cached_transactions.labels(network_num)
        self.total_cached_transactions.set_function(
            functools.partial(len, self._tx_cache_key_to_contents)
        )
        self.total_cached_transactions_size = total_cached_transactions_size.labels(network_num)
        self.total_cached_transactions_size.set_function(
            functools.partial(utils.identity, self._total_tx_contents_size)
        )

    def get_short_id_transaction_type(self, short_id: int) -> TransactionFlag:
        if short_id in self._short_id_to_tx_flag:
            return self._short_id_to_tx_flag[short_id]
        else:
            return TransactionFlag.NO_FLAGS

    def set_short_id_transaction_type(self, short_id: int, tx_flag: TransactionFlag) -> None:
        if TransactionFlag.PAID_TX & tx_flag:
            self._short_id_to_tx_flag[short_id] = tx_flag

    def get_short_id_by_key(self, transaction_key: TransactionKey) -> int:
        """
        Fetches a single short id for transaction. If the transaction has multiple short id mappings, just gets
        the first one.
        :param transaction_key: transaction key
        :return: short id
        """
        return next(iter(self.get_short_ids_by_key(transaction_key)))

    def get_short_ids_by_key(self, transaction_key: TransactionKey) -> Set[int]:
        """
        Fetches all short ids for a given transactions
        :param transaction_key: transaction key
        :return: set of short ids
        """

        if transaction_key.transaction_cache_key in self._tx_cache_key_to_short_ids:
            return self._tx_cache_key_to_short_ids[transaction_key.transaction_cache_key]
        else:
            return constants.NULL_TX_SIDS

    def get_transaction(self, short_id: int) -> TransactionInfo:
        """
        Fetches transaction info for a given short id.
        Results might be None.
        :param short_id:
        :return: transaction hash, transaction contents.
        """
        if short_id in self._short_id_to_tx_cache_key:
            transaction_cache_key = self._short_id_to_tx_cache_key[short_id]
            if transaction_cache_key in self._tx_cache_key_to_contents:
                transaction_contents = self._tx_cache_key_to_contents[transaction_cache_key]
                return TransactionInfo(self._tx_cache_key_to_hash(transaction_cache_key),
                                       transaction_contents,
                                       short_id)
            else:
                return TransactionInfo(self._tx_cache_key_to_hash(transaction_cache_key), None, short_id)
        else:
            return TransactionInfo(None, None, short_id)

    def get_missing_transactions(
        self, short_ids: List[int]
    ) -> Tuple[bool, List[int], List[Sha256Hash]]:
        unknown_tx_sids = []
        unknown_tx_hashes = []
        has_missing = False
        for short_id in short_ids:
            transaction_cache_key = self._short_id_to_tx_cache_key.get(short_id, None)
            if transaction_cache_key is None:
                unknown_tx_sids.append(short_id)
                has_missing = True
                continue
            transaction_key = self.get_transaction_key(None, transaction_cache_key)
            if not self.has_transaction_contents_by_key(transaction_key):
                unknown_tx_hashes.append(transaction_key.transaction_hash)
                has_missing = True
        return has_missing, unknown_tx_sids, unknown_tx_hashes

    def get_transaction_by_key(self, transaction_key: TransactionKey) -> Optional[Union[bytearray, memoryview]]:
        """
        Fetches transaction contents for a given transaction key.
        Results might be None.
        :param transaction_key: transaction key
        :return: transaction contents.
        """
        if transaction_key.transaction_cache_key in self._tx_cache_key_to_contents:
            return self._tx_cache_key_to_contents[transaction_key.transaction_cache_key]

        return None

    def get_transactions(
        self,
        serialized_short_ids: Optional[bytearray] = None
    ) -> TransactionSearchResult:
        """
        Fetches all transaction info for a set of short ids.
        Short ids without a transaction entry will be omitted.
        Function allows to pass a single short id or serialized list of short ids
        :param serialized_short_ids: instance of get transactions message
        :return: list of found and missing short ids
        """

        assert serialized_short_ids is not None
        short_ids = short_ids_serializer.deserialize_short_ids(serialized_short_ids)

        found = []
        missing = []
        for short_id in short_ids:
            if short_id in self._short_id_to_tx_cache_key:
                transaction_cache_key = self._short_id_to_tx_cache_key[short_id]
                if transaction_cache_key in self._tx_cache_key_to_contents:
                    found.append(TransactionInfo(
                        self._tx_cache_key_to_hash(transaction_cache_key),
                        self._tx_cache_key_to_contents[transaction_cache_key],
                        short_id
                    ))
                else:
                    missing.append(TransactionInfo(
                        self._tx_cache_key_to_hash(transaction_cache_key),
                        None,
                        short_id
                    ))
                    logger.trace("Short id {} was requested but is unknown.", short_id)
            else:
                missing.append(TransactionInfo(None, None, short_id))
                logger.trace("Short id {} was requested but is unknown.", short_id)

        return TransactionSearchResult(found, missing)

    def get_tx_hash_to_contents_len(self) -> int:
        return len(self._tx_cache_key_to_contents)

    def get_short_id_count(self) -> int:
        return len(self._short_id_to_tx_cache_key)

    @deprecated
    def has_transaction_contents(self, transaction_hash: Sha256Hash) -> bool:
        """
        Checks if transaction contents is available in transaction service cache

        :param transaction_hash: transaction hash
        :return: Boolean indicating if transaction contents exists
        """
        return self.has_transaction_contents_by_key(self.get_transaction_key(transaction_hash))

    @deprecated
    def has_transaction_contents_by_cache_key(self, cache_key: TransactionCacheKeyType) -> bool:
        """
        Checks if transaction contents is available in transaction service cache

        :param cache_key: transaction cache key
        :return: Boolean indicating if transaction contents exists
        """
        return cache_key in self._tx_cache_key_to_contents

    def has_transaction_contents_by_key(self, transaction_key: TransactionKey) -> bool:
        """
        Checks if transaction contents is available in transaction service cache

        :param transaction_key: transaction key
        :return: Boolean indicating if transaction contents exists
        """
        return transaction_key.transaction_cache_key in self._tx_cache_key_to_contents

    @deprecated
    def has_transaction_short_id(self, transaction_hash: Sha256Hash) -> bool:
        """
        Checks if transaction short id is available in transaction service cache

        :param transaction_hash: transaction hash
        :return: Boolean indicating if transaction short id exists
        """
        return self.has_transaction_short_id_by_key(self.get_transaction_key(transaction_hash))

    def has_transaction_short_id_by_key(self, transaction_key: TransactionKey) -> bool:
        """
        Checks if transaction short id is available in transaction service cache

        :param transaction_key: transaction key
        :return: Boolean indicating if transaction short id exists
        """
        return transaction_key.transaction_cache_key in self._tx_cache_key_to_short_ids

    def has_short_id(self, short_id: int) -> bool:
        """
        Checks if short id is stored in transaction service cache
        :param short_id: transaction short id
        :return: Boolean indicating if short id is found in cache
        """
        return short_id in self._short_id_to_tx_cache_key

    def has_cache_key_no_sid_entry(self, transaction_hash: Sha256Hash) -> bool:
        return transaction_hash in self.tx_hashes_without_short_id.queue

    @deprecated
    def removed_transaction(self, transaction_hash: Sha256Hash) -> bool:
        """
        Check if transaction was seen and removed from cache
        :param transaction_hash: transaction hash
        :return: Boolean indicating in transaction was seen
        """
        return self.removed_transaction_by_key(self.get_transaction_key(transaction_hash))

    @deprecated
    def removed_transaction_by_cache_key(self, cache_key: TransactionCacheKeyType) -> bool:
        """
        Check if transaction was seen and removed from cache
        :param cache_key: transaction cache key
        :return: Boolean indicating in transaction was seen
        """
        return cache_key in self._tx_hash_to_time_removed

    def removed_transaction_by_key(self, transaction_key: TransactionKey) -> bool:
        """
        Check if transaction was seen and removed from cache
        :param transaction_key: transaction key
        :return: Boolean indicating in transaction was seen
        """
        return transaction_key.transaction_cache_key in self._tx_hash_to_time_removed

    @deprecated
    def remove_sid_by_tx_hash(self, transaction_hash: Sha256Hash) -> None:
        self.remove_sid_by_key(self.get_transaction_key(transaction_hash))

    def remove_sid_by_key(self, transaction_key: TransactionKey) -> None:
        if transaction_key.transaction_cache_key in self._tx_cache_key_to_contents:
            logger.trace("attempted to clear sid, for transaction {} with content, ignore", transaction_key)
        else:
            if transaction_key.transaction_cache_key in self._tx_cache_key_to_short_ids:
                short_ids = self._tx_cache_key_to_short_ids[transaction_key.transaction_cache_key]
                del self._tx_cache_key_to_short_ids[transaction_key.transaction_cache_key]
                for short_id in short_ids:
                    del self._short_id_to_tx_cache_key[short_id]
                    self._tx_assignment_expire_queue.remove(short_id)

    @deprecated
    def assign_short_id(
        self,
        transaction_hash: Sha256Hash,
        short_id: int,
        transaction_cache_key: Optional[TransactionCacheKeyType] = None
    ) -> None:
        return self.assign_short_id_by_key(
            self.get_transaction_key(transaction_hash, transaction_cache_key),
            short_id
        )

    def assign_short_id_by_key(
        self,
        transaction_key: TransactionKey,
        short_id: int,
    ) -> None:
        """
        Adds short id mapping for transaction and schedules an alarm to cleanup entry on expiration.
        :param transaction_key: transaction key
        :param short_id: short id to be mapped to transaction
        """
        has_contents = transaction_key.transaction_cache_key in self._tx_cache_key_to_contents
        self.assign_short_id_base_by_key(transaction_key, short_id, has_contents, True)

    @deprecated
    def assign_short_id_base(
        self,
        transaction_hash: Sha256Hash,
        transaction_cache_key: Optional[TransactionCacheKeyType],
        short_id: int,
        has_contents: bool,
        call_to_assign_short_id: bool
    ) -> None:
        return self.assign_short_id_base_by_key(
            self.get_transaction_key(transaction_hash, transaction_cache_key),
            short_id,
            has_contents,
            call_to_assign_short_id
        )

    def assign_short_id_base_by_key(
        self,
        transaction_key: TransactionKey,
        short_id: int,
        has_contents: bool,
        call_to_assign_short_id: bool
    ) -> None:
        """
        Base method to assign short id for a transaction

        :param transaction_key: transaction key object
        :param short_id: transaction short id
        :param has_contents: flag indicating if content already exists in cache for given transaction
        :param call_to_assign_short_id: flag indicating if method should make a call to assign short id form Python code
        :return:
        """
        if short_id == constants.NULL_TX_SID:
            # TODO: this should be an assertion; requires testing
            logger.warning(log_messages.ATTEMPTED_TO_ASSIGN_NULL_SHORT_ID_TO_TX_HASH, transaction_key)
            return
        logger.trace("Assigning sid {} to transaction {}", short_id, transaction_key)

        if not has_contents:
            self.tx_hashes_without_content.add(transaction_key.transaction_hash)
            if not self.tx_without_content_alarm_scheduled:
                self.node.alarm_queue.register_alarm(
                    constants.TX_CONTENT_NO_SID_EXPIRE_S,
                    self.expire_sid_without_content
                )
                self.tx_without_content_alarm_scheduled = True

        if call_to_assign_short_id:
            self._tx_cache_key_to_short_ids[transaction_key.transaction_cache_key].add(short_id)
            self._short_id_to_tx_cache_key[short_id] = transaction_key.transaction_cache_key
        self._tx_assignment_expire_queue.add(short_id)
        self.tx_hashes_without_short_id.remove(transaction_key.transaction_hash)

        if not self.tx_assign_alarm_scheduled:
            self.node.alarm_queue.register_alarm(self.node.opts.sid_expire_time, self.expire_old_assignments)
            self.tx_assign_alarm_scheduled = True

    def set_final_tx_confirmations_count(self, val: int) -> None:
        self._final_tx_confirmations_count = val

    @deprecated
    def set_transaction_contents(
        self, transaction_hash: Sha256Hash, transaction_contents: Union[bytearray, memoryview],
        transaction_cache_key: Optional[TransactionCacheKeyType] = None
    ):
        return self.set_transaction_contents_by_key(
            self.get_transaction_key(transaction_hash, transaction_cache_key),
            transaction_contents
        )

    def set_transaction_contents_by_key(
        self, transaction_key: TransactionKey, transaction_contents: Union[bytearray, memoryview],
    ):
        """
        Adds transaction contents to transaction service cache with lookup key by transaction hash

        :param transaction_key: transaction key object
        :param transaction_contents: transaction contents bytes
        """
        previous_size = 0

        if transaction_key.transaction_cache_key in self._tx_cache_key_to_contents:
            previous_size = len(self._tx_cache_key_to_contents[transaction_key.transaction_cache_key])
        has_short_id = transaction_key.transaction_cache_key in self._tx_cache_key_to_short_ids

        self.set_transaction_contents_base_by_key(
            transaction_key,
            has_short_id,
            previous_size,
            True,
            transaction_contents,
            None
        )

    def set_transaction_contents_base_by_key(
        self,
        transaction_key: TransactionKey,
        has_short_id: bool,
        previous_size: int,
        call_set_contents: bool,
        transaction_contents: Optional[Union[bytearray, memoryview]] = None,
        transaction_contents_length: Optional[int] = None
    ) -> None:
        """
        Adds transaction contents to transaction service cache with lookup key by transaction hash

        :param transaction_key:
        :param has_short_id: flag indicating if cache already has short id for given transaction
        :param previous_size: previous size of transaction contents if already exists
        :param call_set_contents: flag indicating if method should make a call to set content form Python code
        :param transaction_contents: transaction contents bytes
        :param transaction_contents_length: if the transaction contents bytes not available, just send the length
        """
        if not has_short_id:
            self.tx_hashes_without_short_id.add(transaction_key.transaction_hash)
            if not self.tx_content_without_sid_alarm_scheduled:
                self.node.alarm_queue.register_alarm(constants.TX_CONTENT_NO_SID_EXPIRE_S,
                                                     self.expire_content_without_sid)
                self.tx_content_without_sid_alarm_scheduled = True

        self.tx_hashes_without_content.remove(transaction_key.transaction_hash)

        if transaction_contents is not None:
            self._total_tx_contents_size += len(transaction_contents) - previous_size
            if call_set_contents:
                self._tx_cache_key_to_contents[transaction_key.transaction_cache_key] = transaction_contents
        elif transaction_contents_length is not None:
            self._total_tx_contents_size += transaction_contents_length - previous_size
        else:
            logger.debug("both transaction contents and transaction contents length are missing.")

        self._memory_limit_clean_up()

    @deprecated
    def remove_transaction_by_tx_hash(
        self,
        transaction_hash: Sha256Hash,
        force: bool = True,
        assume_no_sid: bool = False
    ) -> Optional[Set[int]]:
        return self.remove_transaction_by_key(self.get_transaction_key(transaction_hash), force, assume_no_sid)

    def remove_transaction_by_key(
        self,
        transaction_key: TransactionKey,
        force: bool = True,
        assume_no_sid: bool = False
    ) -> Optional[Set[int]]:
        """
        Clean up mapping. Removes transaction contents and mapping.
        :param transaction_key: tx key to clean up
        :param force: when false, cleanup will ignore tx / sids marked with tx flag
        :param assume_no_sid: cleanup request will be ignored if the tx has short ids
        """
        removed_sids = 0
        removed_txns = 0

        if transaction_key.transaction_cache_key in self._tx_cache_key_to_short_ids:
            time_removed = time.time()
            short_ids = self._tx_cache_key_to_short_ids[transaction_key.transaction_cache_key]
            if assume_no_sid and short_ids:
                logger.trace("removal of tx {} aborted, ", transaction_key)
                return None
            short_id_flags = [
                self._short_id_to_tx_flag.get(sid, TransactionFlag.NO_FLAGS)
                for sid in short_ids
            ]
            tx_flag = reduce(lambda x, y: x | y, short_id_flags)
            if TransactionFlag.PAID_TX in tx_flag and not force:
                return None
            else:
                short_ids = self._tx_cache_key_to_short_ids.pop(transaction_key.transaction_cache_key)

            for _, short_id in zip(short_id_flags, short_ids):
                tx_stats.add_tx_by_hash_event(
                    transaction_key.transaction_hash, TransactionStatEventType.TX_REMOVED_FROM_MEMORY,
                    self.network_num, short_id, reason=TxRemovalReason.BLOCK_CLEANUP.value
                )
                self._short_id_to_time_removed[short_id] = time_removed
                removed_sids += 1
                if short_id in self._short_id_to_tx_cache_key:
                    del self._short_id_to_tx_cache_key[short_id]
                    if short_id in self._short_id_to_tx_flag:
                        del self._short_id_to_tx_flag[short_id]
                self._tx_assignment_expire_queue.remove(short_id)
                if self.node.opts.dump_removed_short_ids:
                    self._removed_short_ids.add(short_id)
        else:
            short_ids = None

        if transaction_key.transaction_cache_key in self._tx_cache_key_to_contents:
            self._total_tx_contents_size -= len(self._tx_cache_key_to_contents[transaction_key.transaction_cache_key])
            del self._tx_cache_key_to_contents[transaction_key.transaction_cache_key]
            self._tx_hash_to_time_removed[transaction_key.transaction_cache_key] = time.time()
            removed_txns += 1

        logger.trace("Removed transaction: {}, with {} associated short ids and {} contents.", transaction_key,
                     removed_sids, removed_txns)
        return short_ids

    # pylint: disable=too-many-branches
    def remove_transaction_by_short_id(
        self,
        short_id: int,
        remove_related_short_ids: bool = False,
        force: bool = True,
        removal_reason: TxRemovalReason = TxRemovalReason.UNKNOWN
    ) -> None:
        """
        Clean up short id mapping. Removes transaction contents and mapping if only one short id mapping.
        :param short_id: short id to clean up
        :param remove_related_short_ids: remove all other short id for the same tx
        :param force: when false, cleanup will ignore tx / sids marked with tx flag
        :param removal_reason:
        """
        if short_id in self._short_id_to_tx_cache_key:
            time_removed = time.time()
            transaction_cache_key = self._short_id_to_tx_cache_key[short_id]
            if transaction_cache_key in self._tx_cache_key_to_short_ids:
                short_ids = self._tx_cache_key_to_short_ids[transaction_cache_key]
                short_id_flags = [
                    self._short_id_to_tx_flag.get(sid, TransactionFlag.NO_FLAGS)
                    for sid in short_ids
                ]
                tx_flag = reduce(lambda x, y: x | y, short_id_flags)
                if TransactionFlag.PAID_TX in tx_flag and not force:
                    return
            else:
                short_ids = [short_id]

            if self.node.opts.dump_removed_short_ids:
                self._removed_short_ids.add(short_id)

            del self._short_id_to_tx_cache_key[short_id]
            self._short_id_to_time_removed[short_id] = time_removed
            transaction_hash = self._tx_cache_key_to_hash(transaction_cache_key)
            tx_stats.add_tx_by_hash_event(
                transaction_hash, TransactionStatEventType.TX_REMOVED_FROM_MEMORY,
                self.network_num, short_id, reason=removal_reason.value
            )
            # Only clear mapping and txhash_to_contents if last SID assignment
            if len(short_ids) == 1 or remove_related_short_ids:
                for dup_short_id in short_ids:
                    if dup_short_id != short_id:
                        tx_stats.add_tx_by_hash_event(
                            transaction_hash, TransactionStatEventType.TX_REMOVED_FROM_MEMORY,
                            self.network_num, dup_short_id, reason=removal_reason.value
                        )
                        self._short_id_to_time_removed[dup_short_id] = time_removed
                        if dup_short_id in self._short_id_to_tx_cache_key:
                            del self._short_id_to_tx_cache_key[dup_short_id]
                        self._tx_assignment_expire_queue.remove(dup_short_id)
                        if self.node.opts.dump_removed_short_ids:
                            self._removed_short_ids.add(dup_short_id)

                if transaction_cache_key in self._tx_cache_key_to_contents:
                    self._total_tx_contents_size -= len(self._tx_cache_key_to_contents[transaction_cache_key])
                    del self._tx_cache_key_to_contents[transaction_cache_key]
                    self._tx_hash_to_time_removed[transaction_cache_key] = time_removed

                # Delete short ids from _tx_cache_key_to_short_ids after iterating short_ids.
                # Otherwise extension implementation disposes short_ids list after this line
                del self._tx_cache_key_to_short_ids[transaction_cache_key]
                if not remove_related_short_ids:  # TODO : remove this after creating AbstractTransactionService
                    self._track_seen_transaction(transaction_cache_key)
            else:
                short_ids.remove(short_id)

        self._tx_assignment_expire_queue.remove(short_id)

    def iter_transaction_hashes(self) -> Generator[Sha256Hash, None, None]:
        for tx_cache_key in self._tx_cache_key_to_contents:
            yield self._tx_cache_key_to_hash(tx_cache_key)

    def iter_short_ids_seen_in_block(self) -> Generator[Tuple[Sha256Hash, List[int]], None, None]:
        for block_hash, short_ids in self._short_ids_seen_in_block.items():
            yield block_hash, short_ids

    def iter_transaction_hashes_from_oldest(
        self, newest_time: float = float("inf")
    ) -> Generator[Tuple[Sha256Hash, float], None, None]:
        for short_id, timestamp in self._tx_assignment_expire_queue.queue.items():
            if timestamp > newest_time:
                break

            transaction_hash = self.get_transaction(short_id).hash
            assert transaction_hash is not None
            yield transaction_hash, timestamp

    def thread_safe_iter_transactions_from_oldest(
        self, newest_time: float = float("inf")
    ) -> Generator[Tuple[int, Sha256Hash, float], None, None]:

        tries = 0
        items = None

        while tries < 10:
            try:
                items = list(self._tx_assignment_expire_queue.queue.items())
                break
            except RuntimeError:
                tries += 1

        if items is None:
            raise RuntimeError("The expiration queue changed size during iteration every time")

        logger.debug("Attempted to freeze assignment queue {} times", tries)

        for short_id, timestamp in items:
            if timestamp > newest_time:
                break

            if short_id in self._short_id_to_tx_cache_key:
                try:
                    tx_cache_key = self._short_id_to_tx_cache_key[short_id]
                except KeyError:
                    # ignore, probably a concurrency problem removing transactions from a different thread
                    continue
                tx_hash = self._tx_cache_key_to_hash(tx_cache_key)
                yield short_id, tx_hash, timestamp
            else:
                # ignore, probably a concurrency problem removing transactions from a different thread
                continue

    def on_block_cleaned_up(self, block_hash: Sha256Hash) -> None:
        """
        notify the transaction service about a block transactions cleaned from the pool
        :param block_hash: the block sha
        """
        if block_hash in self._short_ids_seen_in_block:
            del self._short_ids_seen_in_block[block_hash]

    def get_short_ids_seen_in_block_count_info(self) -> Tuple[int, int]:
        """
        :return: tuple of number of blocks and total count of short ids seen in all blocks
        """
        total_short_ids_seen_in_blocks = 0
        for _, seen_short_ids_in_block in self._short_ids_seen_in_block.items():
            total_short_ids_seen_in_blocks += len(seen_short_ids_in_block)

        return self.get_tracked_seen_block_count(), total_short_ids_seen_in_blocks

    def get_snapshot(self, duration: float = 0) -> List[Sha256Hash]:
        if duration > 0:
            snapshot_cache_keys = set()
            remove_expired_sids = []
            snapshot_start_from = time.time() - duration
            for short_id, timestamp in self._tx_assignment_expire_queue.queue.items():
                if timestamp > snapshot_start_from:
                    cache_key = self._short_id_to_tx_cache_key.get(short_id, None)
                    if cache_key is not None:
                        snapshot_cache_keys.add(cache_key)
                    else:
                        logger.trace("Short id: {} does not exist!", short_id)
                        remove_expired_sids.append(short_id)
            for short_id in remove_expired_sids:
                self._tx_assignment_expire_queue.remove(short_id)
            return [self._tx_cache_key_to_hash(tx_cache_key) for tx_cache_key in snapshot_cache_keys]
        else:
            return [self._tx_cache_key_to_hash(tx_cache_key) for tx_cache_key in self._tx_cache_key_to_contents]

    def get_tracked_blocks(self, skip_start: int = 0, skip_end: int = 0) -> Dict[Sha256Hash, int]:
        """
        get a dictionary of tracked seen blocks from start until the reaching a certain number from the end,
        since we want to clear the oldest blocks we already seen.
        :param skip_start: the amount of blocks to skip from start
        :param skip_end: the amount of blocks to skip from the end
        :return: a dictionary of seen blocks mapped to their index relative to the start
        """
        tracked_blocks = {}
        for idx, block in enumerate(self._iter_block_seen_by_time(skip_start, skip_end)):
            tracked_blocks[block] = idx
        return tracked_blocks

    def get_oldest_tracked_block(self, skip_block_count: int) -> List[Sha256Hash]:
        """
        get a list of tracked seen blocks from start until the reaching a certain number from the end,
        since we want to clear the oldest blocks we already seen.
        :param skip_block_count: the amount of blocks to skip from the end (the newest block)
        :return: a list of seen blocks from oldest to latest
        """
        return list(self._iter_block_seen_by_time(0, skip_block_count))

    def get_tracked_seen_block_count(self) -> int:
        return len(self._short_ids_seen_in_block)

    def get_short_id_assign_time(self, short_id: int) -> float:
        if short_id in self._tx_assignment_expire_queue.queue:
            return self._tx_assignment_expire_queue.queue[short_id]
        else:
            logger.warning(log_messages.MISSING_ASSIGN_TIME_FOR_SHORT_ID, short_id)
            return 0.0

    def expire_old_assignments(self) -> float:
        """
        Clean up expired short ids.
        """
        logger.debug("Expiring old short id assignments. Total entries: {}",
                     len(self._tx_assignment_expire_queue))
        self._tx_assignment_expire_queue.remove_expired(
            remove_callback=self.remove_transaction_by_short_id,
            limit=constants.MAX_EXPIRED_TXS_TO_REMOVE,
            force=True,
            removal_reason=TxRemovalReason.EXPIRATION
        )
        logger.debug("Finished cleaning up short ids. Entries remaining: {}",
                     len(self._tx_assignment_expire_queue))
        if len(self._tx_assignment_expire_queue) > 0:
            oldest_tx_timestamp = self._tx_assignment_expire_queue.get_oldest_item_timestamp()
            assert oldest_tx_timestamp is not None
            time_to_expire_oldest = (oldest_tx_timestamp + self.node.opts.sid_expire_time) - time.time()
            return max(time_to_expire_oldest, constants.MIN_CLEAN_UP_EXPIRED_TXS_TASK_INTERVAL_S)
        else:
            self.tx_assign_alarm_scheduled = False
            return 0

    def expire_content_without_sid(self) -> float:
        """
        Clean up content without short ids.
        """
        logger.debug("Expiring tx content for tx without sid. Total entries: {}",
                     len(self.tx_hashes_without_short_id))
        self.tx_hashes_without_short_id.remove_expired(
            remove_callback=self.remove_transaction_by_tx_hash,
            limit=constants.MAX_EXPIRED_TXS_TO_REMOVE,
            force=True,
            assume_no_sid=True
        )
        logger.debug("Finished cleaning up tx. Entries remaining: {}",
                     len(self.tx_hashes_without_short_id))
        if len(self.tx_hashes_without_short_id) > 0:
            oldest_tx_timestamp = self.tx_hashes_without_short_id.get_oldest_item_timestamp()
            assert oldest_tx_timestamp is not None
            time_to_expire_oldest = (oldest_tx_timestamp + constants.TX_CONTENT_NO_SID_EXPIRE_S) - time.time()
            return max(time_to_expire_oldest, constants.MIN_CLEAN_UP_EXPIRED_TXS_TASK_INTERVAL_S)
        else:
            self.tx_content_without_sid_alarm_scheduled = False
            return 0

    def expire_sid_without_content(self) -> float:
        """
        Clean up short ids without content.
        """
        logger.debug("Expiring short ids without content. Total entries: {}",
                     len(self.tx_hashes_without_content))
        self.tx_hashes_without_content.remove_expired(
            remove_callback=self.remove_sid_by_tx_hash,
            limit=constants.MAX_EXPIRED_TXS_TO_REMOVE,
        )
        logger.debug("Finished cleaning up sids. Entries remaining: {}",
                     len(self.tx_hashes_without_content))
        if len(self.tx_hashes_without_content) > 0:
            oldest_tx_timestamp = self.tx_hashes_without_content.get_oldest_item_timestamp()
            assert oldest_tx_timestamp is not None
            time_to_expire_oldest = (oldest_tx_timestamp + constants.TX_CONTENT_NO_SID_EXPIRE_S) - time.time()
            return max(time_to_expire_oldest, constants.MIN_CLEAN_UP_EXPIRED_TXS_TASK_INTERVAL_S)
        else:
            self.tx_without_content_alarm_scheduled = False
            return 0

    def track_seen_short_ids(self, block_hash: Sha256Hash, short_ids: List[int]) -> None:
        """
        Track short ids that has been seen in a routed block.
        That information helps transaction service make a decision when to remove transactions from cache.

        :param block_hash: block hash of the tx short ids
        :param short_ids: transaction short ids
        """

        wrapped_block_hash = wrap_sha256(block_hash)
        self._short_ids_seen_in_block[wrapped_block_hash] = short_ids

        if len(self._short_ids_seen_in_block) >= self._final_tx_confirmations_count:

            # pyre-fixme[28]: Unexpected keyword argument `last`.
            _, final_short_ids = self._short_ids_seen_in_block.popitem(last=False)

            for short_id in final_short_ids:
                self.remove_transaction_by_short_id(short_id, remove_related_short_ids=True, force=True,
                                                    removal_reason=TxRemovalReason.BLOCK_CLEANUP)

        logger_memory_cleanup.statistics(
            {
                "type": "MemoryCleanup",
                "event": "TransactionServiceTrackSeenSummary",
                "data": self.get_cache_state_json(),
                "seen_short_ids_count": len(short_ids),
                "block_hash": repr(block_hash)
            }
        )

    def track_seen_short_ids_delayed(self, block_hash: Sha256Hash, short_ids: List[int]) -> None:
        """
        Schedules alarm task to clean up seen short ids after some delay
        :param block_hash: block hash
        :param short_ids: transaction short ids
        :return:
        """

        self.node.alarm_queue.register_alarm(
            constants.CLEAN_UP_SEEN_SHORT_IDS_DELAY_S,
            self.track_seen_short_ids,
            block_hash,
            short_ids
        )

    def process_tx_sync_message(self, msg: TxServiceSyncTxsMessage) -> List[TxSyncMsgProcessingItem]:
        result_items = []
        txs_content_short_ids = msg.txs_content_short_ids()
        for tx_content_short_ids in txs_content_short_ids:
            transaction_key = self.get_transaction_key(tx_content_short_ids.tx_hash)

            tx_content = tx_content_short_ids.tx_content
            tx_content_len = 0

            if tx_content:
                tx_content_len = len(tx_content)
                self.set_transaction_contents_by_key(transaction_key, tx_content)

            for short_id, _ in zip(
                tx_content_short_ids.short_ids, tx_content_short_ids.short_id_flags
            ):
                self.assign_short_id_by_key(transaction_key, short_id)

            result_item = TxSyncMsgProcessingItem(transaction_key.transaction_hash,
                                                  tx_content_len,
                                                  tx_content_short_ids.short_ids,
                                                  tx_content_short_ids.short_id_flags)
            result_items.append(result_item)

        return result_items

    def log_block_transaction_cleanup_stats(self, block_hash: Sha256Hash, tx_count: int, tx_before_cleanup: int,
                                            tx_after_cleanup: int, short_id_count_before_cleanup: int,
                                            short_id_count_after_cleanup: int):
        logger_memory_cleanup.statistics(
            {
                "type": "BlockTransactionsCleanup",
                "block_hash": repr(block_hash),
                "block_transactions_count": tx_count,
                "tx_hash_to_contents_len_before_cleanup": tx_before_cleanup,
                "tx_hash_to_contents_len_after_cleanup": tx_after_cleanup,
                "short_id_count_before_cleanup": short_id_count_before_cleanup,
                "short_id_count_after_cleanup": short_id_count_after_cleanup,
            }
        )

    def log_tx_service_mem_stats(self, include_data_structure_memory: bool = False) -> None:
        """
        Logs transactions service memory statistics
        """
        if self.node.opts.stats_calculate_actual_size and include_data_structure_memory:
            size_type = memory_utils.SizeType.OBJECT
        else:
            size_type = memory_utils.SizeType.ESTIMATE

        class_name = self.__class__.__name__
        hooks.add_obj_mem_stats(
            class_name,
            self.network_num,
            self._tx_cache_key_to_contents,
            "tx_cache_key_to_contents",
            self.get_collection_mem_stats(
                size_type,
                self._tx_cache_key_to_contents,
                self.ESTIMATED_TX_HASH_ITEM_SIZE * len(self._tx_cache_key_to_contents) + self._total_tx_contents_size
            ),
            object_item_count=len(self._tx_cache_key_to_contents),
            object_type=self.get_object_type(self._tx_cache_key_to_contents),
            size_type=size_type
        )
        hooks.add_obj_mem_stats(
            class_name,
            self.network_num,
            self._short_id_to_tx_cache_key,
            "short_id_to_tx_cache_key",
            self.get_collection_mem_stats(
                size_type,
                self._short_id_to_tx_cache_key,
                self.ESTIMATED_TX_HASH_AND_SHORT_ID_ITEM_SIZE * len(self._short_id_to_tx_cache_key)
            ),
            object_item_count=len(self._short_id_to_tx_cache_key),
            object_type=self.get_object_type(self._short_id_to_tx_cache_key),
            size_type=size_type
        )

        if include_data_structure_memory:
            hooks.add_obj_mem_stats(
                class_name,
                self.network_num,
                self._tx_cache_key_to_short_ids,
                "tx_cache_key_to_short_ids",
                self.get_collection_mem_stats(
                    size_type,
                    self._tx_cache_key_to_short_ids,
                    self.ESTIMATED_TX_HASH_AND_SHORT_ID_ITEM_SIZE * len(self._tx_cache_key_to_short_ids)
                ),
                object_item_count=len(self._tx_cache_key_to_short_ids),
                object_type=self.get_object_type(self._tx_cache_key_to_short_ids),
                size_type=size_type
            )
            hooks.add_obj_mem_stats(
                class_name,
                self.network_num,
                self._short_ids_seen_in_block,
                "short_ids_seen_in_block",
                self.get_collection_mem_stats(
                    size_type,
                    self._short_ids_seen_in_block,
                    self.ESTIMATED_TX_HASH_AND_SHORT_ID_ITEM_SIZE * len(self._short_ids_seen_in_block)
                ),
                object_item_count=len(self._short_ids_seen_in_block),
                object_type=memory_utils.ObjectType.BASE,
                size_type=size_type
            )
            hooks.add_obj_mem_stats(
                class_name,
                self.network_num,
                self._tx_assignment_expire_queue,
                "tx_assignment_expire_queue",
                self.get_collection_mem_stats(
                    size_type,
                    self._tx_assignment_expire_queue,
                    self.ESTIMATED_SHORT_ID_EXPIRATION_ITEM_SIZE * len(self._tx_assignment_expire_queue)
                ),
                object_item_count=len(self._tx_assignment_expire_queue),
                object_type=memory_utils.ObjectType.BASE,
                size_type=size_type
            )

            hooks.add_obj_mem_stats(
                class_name,
                self.network_num,
                self._removed_short_ids,
                "removed_short_ids",
                self.get_collection_mem_stats(
                    size_type,
                    self._removed_short_ids,
                    len(self._removed_short_ids) * constants.SID_LEN
                ),
                object_item_count=len(self._removed_short_ids),
                object_type=memory_utils.ObjectType.BASE,
                size_type=size_type
            )

            hooks.add_obj_mem_stats(
                class_name,
                self.network_num,
                self._tx_hash_to_time_removed,
                "tx_hash_to_time_removed",
                self.get_collection_mem_stats(
                    size_type,
                    self._tx_hash_to_time_removed,
                    len(self._tx_hash_to_time_removed) * SHA256_HASH_LEN
                ),
                object_item_count=len(self._tx_hash_to_time_removed),
                object_type=memory_utils.ObjectType.BASE,
                size_type=size_type
            )

            hooks.add_obj_mem_stats(
                class_name,
                self.network_num,
                self._short_id_to_time_removed,
                "_short_id_to_time_removed",
                self.get_collection_mem_stats(
                    size_type,
                    self._short_id_to_time_removed,
                    len(self._short_id_to_time_removed) * constants.SID_LEN
                ),
                object_item_count=len(self._short_id_to_time_removed),
                object_type=memory_utils.ObjectType.BASE,
                size_type=size_type
            )

            hooks.add_obj_mem_stats(
                class_name,
                self.network_num,
                self.tx_hashes_without_short_id,
                "tx_hash_without_sid",
                self.get_collection_mem_stats(
                    size_type,
                    self.tx_hashes_without_short_id,
                    len(self.tx_hashes_without_short_id) * SHA256_HASH_LEN
                ),
                object_item_count=len(self.tx_hashes_without_short_id),
                object_type=memory_utils.ObjectType.BASE,
                size_type=size_type
            )

            hooks.add_obj_mem_stats(
                class_name,
                self.network_num,
                self.tx_hashes_without_content,
                "tx_hash_sid_without_content",
                self.get_collection_mem_stats(
                    size_type,
                    self.tx_hashes_without_content,
                    len(self.tx_hashes_without_content) * SHA256_HASH_LEN
                ),
                object_item_count=len(self.tx_hashes_without_content),
                object_type=memory_utils.ObjectType.BASE,
                size_type=size_type
            )

    def get_object_type(
        self,
        collection_obj: Any  # pylint: disable=unused-argument
    ):
        return memory_utils.ObjectType.BASE

    def get_aggregate_stats(self) -> Dict[str, Any]:
        """
        Returns dictionary with aggregated statistics of transactions service

        :return: dictionary with aggregated statistics
        """
        oldest_transaction_date = 0
        oldest_transaction_hash = ""

        if len(self._tx_assignment_expire_queue.queue) > 0:
            oldest_transaction_date = self._tx_assignment_expire_queue.get_oldest_item_timestamp()
            oldest_transaction_sid = self._tx_assignment_expire_queue.get_oldest()
            if oldest_transaction_sid in self._short_id_to_tx_cache_key:
                oldest_transaction_hash = self._short_id_to_tx_cache_key[oldest_transaction_sid]

        current_stats = TransactionServiceStats(
            len(self._short_id_to_tx_cache_key),
            len(self._tx_cache_key_to_contents),
            self._total_tx_removed_by_memory_limit,
            self._total_tx_contents_size
        )

        difference = current_stats - self._last_transaction_stats
        self._last_transaction_stats = current_stats

        return {
            "oldest_transaction_date": oldest_transaction_date,
            "oldest_transaction_hash": oldest_transaction_hash,
            "aggregate": current_stats.__dict__,
            "delta": difference.__dict__
        }

    def get_collection_mem_stats(self, size_type: SizeType, collection_obj: Any, estimated_size: int = 0) -> ObjectSize:
        if size_type == SizeType.OBJECT:
            return memory_utils.get_object_size(collection_obj)
        else:
            return ObjectSize(size=estimated_size, flat_size=0, is_actual_size=False)

    def get_cache_state_json(self) -> Dict[str, Any]:
        return {
            "tx_hash_to_short_ids_len": len(self._tx_cache_key_to_short_ids),
            "short_id_to_tx_hash_len": len(self._short_id_to_tx_cache_key),
            "tx_hash_to_contents_len": len(self._tx_cache_key_to_contents),
            "short_ids_seen_in_block_len": len(self._short_ids_seen_in_block),
            "total_tx_contents_size": self._total_tx_contents_size,
            "network_num": self.network_num
        }

    def get_cache_state_str(self) -> str:
        return json_encoder.to_json(self.get_cache_state_json())

    def get_removed_tx_hash_time_and_count(self, tx_hashes: List[Sha256Hash]) -> Tuple[float, int]:
        oldest_removed_tx_hash = 0
        removed_tx_hash_count = 0
        for tx_hash in tx_hashes:
            if tx_hash in self._tx_hash_to_time_removed:
                removed_tx_hash_count += 1
                if oldest_removed_tx_hash < self._tx_hash_to_time_removed[tx_hash]:
                    oldest_removed_tx_hash = self._tx_hash_to_time_removed[tx_hash]
        return oldest_removed_tx_hash, removed_tx_hash_count

    def get_removed_short_id_time_and_count(self, short_ids: List[int]) -> Tuple[float, int]:
        oldest_removed_short_id = 0
        removed_short_id_count = 0
        for short_id in short_ids:
            if short_id in self._short_id_to_time_removed:
                removed_short_id_count += 1
                if oldest_removed_short_id < self._short_id_to_time_removed[short_id]:
                    oldest_removed_short_id = self._short_id_to_time_removed[short_id]
        return oldest_removed_short_id, removed_short_id_count

    def get_transaction_key(
        self,
        transaction_hash: Optional[Sha256Hash],
        transaction_cache_key: Optional[TransactionCacheKeyType] = None
    ) -> TransactionKey:
        if transaction_hash is None:
            assert transaction_cache_key is not None
            transaction_hash = self._tx_cache_key_to_hash(transaction_cache_key)

        transaction_hash = wrap_sha256(transaction_hash)
        return TransactionKey(
            transaction_hash,
            transaction_cache_key,
            _lazy_transaction_cache_key=iter((self._tx_hash_to_cache_key(transaction_hash)) for _ in iter((None,)))
        )

    def _dump_removed_short_ids(self) -> int:
        if self._removed_short_ids:
            with open(f"{self.node.opts.dump_removed_short_ids_path}/{int(time.time())}", "w") as file_handle:
                file_handle.write(str(self._removed_short_ids))
            self._removed_short_ids.clear()
        return constants.DUMP_REMOVED_SHORT_IDS_INTERVAL_S

    def _memory_limit_clean_up(self) -> None:
        """
        Removes oldest transactions if total bytes consumed by transaction contents exceed memory limit
        """
        if self._total_tx_contents_size <= self._tx_content_memory_limit:
            return

        logger.trace("Transaction service exceeds memory limit for transaction contents. Limit: {}. Current size: {}.",
                     self._tx_content_memory_limit, self._total_tx_contents_size)
        removed_tx_count = 0

        while self._is_exceeding_memory_limit() and self._tx_assignment_expire_queue:
            self._tx_assignment_expire_queue.remove_oldest(
                remove_callback=self.remove_transaction_by_short_id,
                removal_reason=TxRemovalReason.MEMORY_LIMIT
            )
            removed_tx_count += 1
        if self._is_exceeding_memory_limit() and not self._tx_assignment_expire_queue:
            logger.warning(log_messages.SID_MEMORY_MANAGEMENT_FAILURE, self.get_cache_state_json())
            removed_tx_count += len(self._tx_cache_key_to_contents)
            self.clear()

        self._total_tx_removed_by_memory_limit += removed_tx_count
        logger.trace("Removed {} oldest transactions from transaction service cache. Size after clean up: {}",
                     removed_tx_count, self._total_tx_contents_size)

    def _get_final_tx_confirmations_count(self) -> int:
        """
        Returns configuration value of number of block confirmations required before transaction can be removed
        """
        if self.network:
            return self.network.final_tx_confirmations_count

        logger.warning(
            log_messages.UNABLE_TO_DETERMINE_TX_FINAL_CONFIRMATIONS_COUNT,
            self.network_num, self.DEFAULT_FINAL_TX_CONFIRMATIONS_COUNT
        )

        return self.DEFAULT_FINAL_TX_CONFIRMATIONS_COUNT

    def _get_removed_transactions_history_expiration_time_s(self) -> int:
        """
        Returns configuration value of expiration time for transaction hashes removed from cache
        """
        if self.network:
            return self.network.removed_transactions_history_expiration_s

        logger.warning(
            log_messages.UNABLE_TO_DETERMINE_TX_EXPIRATION_TIME,
            self.network_num, constants.REMOVED_TRANSACTIONS_HISTORY_EXPIRATION_S
        )

        return constants.REMOVED_TRANSACTIONS_HISTORY_EXPIRATION_S

    def _get_tx_contents_memory_limit(self) -> int:
        """
        Returns configuration value for memory limit for total transaction contents
        """
        if self.node.opts.transaction_pool_memory_limit is not None:
            # convert MB to bytes
            return int(self.node.opts.transaction_pool_memory_limit * 1024 * 1024)

        if self.network:
            if self.network.tx_contents_memory_limit_bytes is None:
                logger.warning(
                    log_messages.TX_CACHE_SIZE_LIMIT_NOT_CONFIGURED,
                    self.network_num, constants.DEFAULT_TX_CACHE_MEMORY_LIMIT_BYTES
                )
                return constants.DEFAULT_TX_CACHE_MEMORY_LIMIT_BYTES
            else:
                return self.network.tx_contents_memory_limit_bytes

        logger.warning(
            log_messages.UNABLE_TO_DETERMINE_TX_MEMORY_LIMIT,
            self.network_num, constants.DEFAULT_TX_CACHE_MEMORY_LIMIT_BYTES
        )
        return constants.DEFAULT_TX_CACHE_MEMORY_LIMIT_BYTES

    def _tx_hash_to_cache_key(self, transaction_hash: Union[Sha256Hash, bytes, bytearray, memoryview, str]) -> str:

        if isinstance(transaction_hash, Sha256Hash):
            return convert.bytes_to_hex(transaction_hash.binary)

        if isinstance(transaction_hash, (bytes, bytearray, memoryview)):
            return convert.bytes_to_hex(transaction_hash)

        # pyre-fixme[25]: Assertion will always fail.
        if isinstance(transaction_hash, str):
            return transaction_hash

        raise ValueError("Attempted to find cache entry with incorrect key type")

    def _wrap_sha256(self, transaction_hash: Union[bytes, bytearray, memoryview, Sha256Hash]) -> Sha256Hash:
        if isinstance(transaction_hash, Sha256Hash):
            return transaction_hash

        # pyre-fixme[25]: Assertion will always fail.
        if isinstance(transaction_hash, (bytes, bytearray, memoryview)):
            return Sha256Hash(binary=transaction_hash)

        return Sha256Hash(binary=convert.hex_to_bytes(transaction_hash))

    def _tx_cache_key_to_hash(self, transaction_cache_key: TransactionCacheKeyType) -> Sha256Hash:
        if isinstance(transaction_cache_key, Sha256Hash):
            return transaction_cache_key

        if isinstance(transaction_cache_key, (bytes, bytearray, memoryview)):
            return Sha256Hash(transaction_cache_key)

        # pyre-fixme[6]:
        return Sha256Hash(convert.hex_to_bytes(transaction_cache_key))

    def _track_seen_transaction(self, transaction_cache_key):
        pass

    def _iter_block_seen_by_time(self, skip_start: int, skip_end: int) -> Iterator[Sha256Hash]:
        end = len(self._short_ids_seen_in_block) - skip_end
        for idx, block_hash in enumerate(self._short_ids_seen_in_block.keys()):
            if skip_start <= idx <= end:
                yield block_hash

    def _is_exceeding_memory_limit(self) -> bool:
        return self._total_tx_contents_size > self._tx_content_memory_limit

    def clear(self) -> None:
        self._tx_cache_key_to_contents.clear()
        self._tx_cache_key_to_short_ids.clear()
        self._short_id_to_tx_cache_key.clear()
        self._short_ids_seen_in_block.clear()
        self._short_id_to_tx_flag.clear()
        self.tx_hashes_without_content.clear()
        self.tx_hashes_without_short_id.clear()
        self._tx_assignment_expire_queue.clear()
        self._total_tx_contents_size = 0

    # TODO: remove this unused function
    def _log_transaction_service_histogram(self) -> None:
        """
        logs a histogram of the tracked transactions age,
        buckets are named as according to the age in hours from now
        bucket is named according the the range start

        """
        bucket_count = constants.TRANSACTION_SERVICE_TRANSACTIONS_HISTOGRAM_BUCKETS
        cell_size = self.node.opts.sid_expire_time / bucket_count
        cell_size_hours = cell_size / (60 * 60)
        histogram = Counter()
        current_time = time.time()
        timestamps = self._tx_assignment_expire_queue.queue.values()
        for timestamp in timestamps:
            histogram[int((timestamp // cell_size) * cell_size)] += 1
        logger_tx_histogram.statistics(
            {"type": "TransactionHistogram",
             "data": {datetime.fromtimestamp(k): v for (k, v) in histogram.items()},
             "start_time": datetime.utcnow(),
             "duration": time.time() - current_time,
             "cell_size_s": cell_size,
             "cell_size_h": cell_size_hours,
             "network_num": self.network_num
             }
        )
        return constants.TRANSACTION_SERVICE_LOG_TRANSACTIONS_INTERVAL_S

    def _cleanup_removed_transactions_history(self) -> int:
        """
        Removes expired items from the queue
        """
        logger.trace(
            "Starting to cleanup transaction cache history for network "
            "number: {}.",
            self.network_num
        )

        current_time = time.time()
        tx_hash_history_len_before = len(self._tx_hash_to_time_removed)
        if self._tx_hash_to_time_removed:
            oldest_tx = next(iter(self._tx_hash_to_time_removed))
            while (self._tx_hash_to_time_removed and
                   ((current_time - self._tx_hash_to_time_removed[oldest_tx] > self._removed_txs_expiration_time_s) or
                    len(self._tx_hash_to_time_removed) > constants.REMOVED_TRANSACTIONS_HISTORY_LENGTH_LIMIT)):
                del self._tx_hash_to_time_removed[oldest_tx]
                if not self._tx_hash_to_time_removed:
                    break
                oldest_tx = next(iter(self._tx_hash_to_time_removed))
        tx_hash_history_len_after = len(self._tx_hash_to_time_removed)

        short_id_history_len_before = len(self._short_id_to_time_removed)
        if self._short_id_to_time_removed:
            oldest_short_id = next(iter(self._short_id_to_time_removed))
            while (self._short_id_to_time_removed and
                   ((current_time - self._short_id_to_time_removed[oldest_short_id] >
                     self._removed_txs_expiration_time_s) or
                    len(self._short_id_to_time_removed) > constants.REMOVED_TRANSACTIONS_HISTORY_LENGTH_LIMIT)):
                del self._short_id_to_time_removed[oldest_short_id]
                if not self._short_id_to_time_removed:
                    break
                oldest_short_id = next(iter(self._short_id_to_time_removed))
        short_id_history_len_after = len(self._short_id_to_time_removed)

        logger.trace(
            "Finished cleanup transaction cache history. "
            "tx_hash size before: {}, size after: {}."
            "short_id size before: {}, size after: {}.",
            tx_hash_history_len_before,
            tx_hash_history_len_after,
            short_id_history_len_before,
            short_id_history_len_after
        )

        return constants.REMOVED_TRANSACTIONS_HISTORY_CLEANUP_INTERVAL_S
