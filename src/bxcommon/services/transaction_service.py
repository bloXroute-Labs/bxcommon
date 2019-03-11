from collections import defaultdict, deque

from bxcommon import constants
from bxcommon.utils import logger, memory_utils
from bxcommon.utils.expiration_queue import ExpirationQueue
from bxcommon.utils.memory_utils import ObjectSize
from bxcommon.utils.stats import hooks


class TransactionService(object):
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
    _tx_hash_to_short_ids: mapping of transaction long hashes to (potentially multiple) short ids
    _short_id_to_tx_hash: mapping of short id to transaction long hashes
    _tx_hash_to_contents: mapping of transaction long hashes to transaction contents
    _tx_assignment_expire_queue: expiration time of short ids
    """

    MAX_ID = 2 ** 32
    SHORT_ID_SIZE = 4
    DEFAULT_FINAL_TX_CONFIRMATIONS_COUNT = 24
    DEFAULT_TX_MEMORY_LIMIT = 200 * 1024 * 1024

    def __init__(self, node, network_num):
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

        self._tx_hash_to_short_ids = defaultdict(set)
        self._short_id_to_tx_hash = {}
        self._tx_hash_to_contents = {}
        self._tx_assignment_expire_queue = ExpirationQueue(node.opts.sid_expire_time)

        self._final_tx_confirmations_count = self._get_final_tx_confirmations_count()
        self._tx_content_memory_limit = self._get_tx_contents_memory_limit()

        # deque of short ids in blocks in the order they are received
        self._short_ids_seen_in_block = deque()

        self._total_tx_contents_size = 0
        self._total_tx_removed_by_memory_limit = 0

    def set_transaction_contents(self, transaction_hash, transaction_contents):
        """
        Adds transaction contents to transaction service cache with lookup key by transaction hash

        :param transaction_hash: transaction hash
        :param transaction_contents: transaction contents bytes
        """

        previous_size = 0

        if transaction_hash in self._tx_hash_to_contents:
            previous_size = len(self._tx_hash_to_contents[transaction_hash])

        self._tx_hash_to_contents[transaction_hash] = transaction_contents
        self._total_tx_contents_size += len(transaction_contents) - previous_size

        self._memory_limit_clean_up()

    def has_transaction_contents(self, transaction_hash):
        """
        Checks if transaction contents is available in transaction service cache

        :param transaction_hash: transaction hash
        :return: Boolean indicating if transaction contents exists
        """

        return transaction_hash in self._tx_hash_to_contents

    def has_transaction_short_id(self, transaction_hash):
        """
        Checks if transaction short id is available in transaction service cache

        :param transaction_hash: transaction hash
        :return: Boolean indicating if transaction short id exists
        """

        return transaction_hash in self._tx_hash_to_short_ids

    def has_short_id(self, short_id):
        """
        Checks if short id is stored in transaction service cache
        :param short_id: transaction short id
        :return: Boolean indicating if short id is found in cache
        """

        return short_id in self._short_id_to_tx_hash

    def assign_short_id(self, transaction_hash, short_id):
        """
        Adds short id mapping for transaction and schedules an alarm to cleanup entry on expiration.
        :param transaction_hash: transaction long hash
        :param short_id: short id to be mapped to transaction
        """
        if short_id == constants.NULL_TX_SID:
            logger.warn("Attempt to assign null SID to transaction hash {}. Ignoring.".format(transaction_hash))
            return
        logger.debug("Assigning sid {} to transaction {}".format(short_id, transaction_hash))
        self._tx_hash_to_short_ids[transaction_hash].add(short_id)
        self._short_id_to_tx_hash[short_id] = transaction_hash
        self._tx_assignment_expire_queue.add(short_id)

        if not self.tx_assign_alarm_scheduled:
            self.node.alarm_queue.register_alarm(self.node.opts.sid_expire_time, self.expire_old_assignments)
            self.tx_assign_alarm_scheduled = True

    def get_short_id(self, transaction_hash):
        """
        Fetches a single short id for transaction. If the transaction has multiple short id mappings, just gets
        the first one.
        :param transaction_hash: transaction long hash
        :return: short id
        """
        return next(iter(self.get_short_ids(transaction_hash)))

    def get_short_ids(self, transaction_hash):
        """
        Fetches all short ids for a given transactions
        :param transaction_hash: transaction long hash
        :return: set of short ids
        """
        if transaction_hash in self._tx_hash_to_short_ids:
            return self._tx_hash_to_short_ids[transaction_hash]
        else:
            return {constants.NULL_TX_SID}

    def get_transaction(self, short_id):
        """
        Fetches transaction info for a given short id.
        Results might be None.
        :param short_id:
        :return: transaction hash, transaction contents.
        """
        if short_id in self._short_id_to_tx_hash:
            transaction_hash = self._short_id_to_tx_hash[short_id]
            if transaction_hash in self._tx_hash_to_contents:
                return transaction_hash, self._tx_hash_to_contents[transaction_hash]
            else:
                return transaction_hash, None
        else:
            return None, None

    def get_transaction_by_hash(self, transaction_hash):
        """
        Fetches transaction contents for a given transaction hash.
        Results might be None.
        :param transaction_hash: transaction hash
        :return: transaction contents.
        """

        if transaction_hash in self._tx_hash_to_contents:
            return self._tx_hash_to_contents[transaction_hash]

        return None

    def get_transactions(self, short_ids):
        """
        Fetches all transaction info for a set of short ids.
        Short ids without a transaction entry will be omitted.
        :param short_ids: list of short ids
        :return: list of (transaction hash, transaction contents)
        """
        transactions = []
        for short_id in short_ids:
            if short_id in self._short_id_to_tx_hash:
                transaction_hash = self._short_id_to_tx_hash[short_id]
                if transaction_hash in self._tx_hash_to_contents:
                    tx = self._tx_hash_to_contents[transaction_hash]
                    transactions.append((short_id, transaction_hash, tx))
                else:
                    logger.debug("Short id {} was requested but is unknown.".format(short_id))
            else:
                logger.debug("Short id {} was requested but is unknown.".format(short_id))

        return transactions

    def expire_old_assignments(self):
        """
        Clean up expired short ids.
        """
        logger.info(
            "Expiring old short id assignments. Total entries: {}".format(len(self._tx_assignment_expire_queue)))
        self._tx_assignment_expire_queue.remove_expired(remove_callback=self._remove_transaction_by_short_id)
        logger.info(
            "Finished cleaning up short ids. Entries remaining: {}".format(len(self._tx_assignment_expire_queue)))
        if len(self._tx_assignment_expire_queue) > 0:
            return self.node.opts.sid_expire_time
        else:
            self.tx_assign_alarm_scheduled = False
            return 0

    def track_seen_short_ids(self, short_ids):
        """
        Track short ids that has been seen in a routed block.
        That information helps transaction service make a decision when to remove transactions from cache.

        :param short_ids: transaction short ids
        """

        if short_ids is None:
            return ValueError("short_ids is required.")

        self._short_ids_seen_in_block.append(short_ids)

        if len(self._short_ids_seen_in_block) > self._final_tx_confirmations_count:

            final_short_ids = self._short_ids_seen_in_block.popleft()

            for short_id in final_short_ids:
                self._remove_transaction_by_short_id(short_id)

    def log_tx_service_mem_stats(self):
        """
        Logs transactions service memory statistics
        """

        class_name = self.__class__.__name__
        hooks.add_obj_mem_stats(
            class_name,
            self.network_num,
            self._tx_hash_to_short_ids,
            "tx_hash_to_short_ids",
            self.get_collection_mem_stats(self._tx_hash_to_short_ids))

        hooks.add_obj_mem_stats(
            class_name,
            self.network_num,
            self._tx_hash_to_contents,
            "tx_hash_to_contents",
            self.get_collection_mem_stats(self._tx_hash_to_contents))

        hooks.add_obj_mem_stats(
            class_name,
            self.network_num,
            self._short_id_to_tx_hash,
            "short_id_to_tx_hash",
            self.get_collection_mem_stats(self._short_id_to_tx_hash))

        hooks.add_obj_mem_stats(
            class_name,
            self.network_num,
            self._short_ids_seen_in_block,
            "short_ids_seen_in_block",
            self.get_collection_mem_stats(self._short_ids_seen_in_block))

    def get_tx_service_aggregate_stats(self):
        """
        Returns dictionary with aggregated statistics of transactions service

        :return: dictionary with aggregated statistics
        """

        if len(self._tx_assignment_expire_queue.queue) > 0:
            oldest_transaction_date = self._tx_assignment_expire_queue.queue[0][0]
        else:
            oldest_transaction_date = 0
        return dict(
            short_id_mapping_count_gauge=len(self._short_id_to_tx_hash),
            unique_transaction_content_gauge=len(self._tx_hash_to_contents),
            oldest_transaction_date=oldest_transaction_date,
            transactions_removed_by_memory_limit=self._total_tx_removed_by_memory_limit
        )

    def get_collection_mem_stats(self, collection_obj, ):
        if self.node.opts.stats_calculate_actual_size:
            return memory_utils.get_object_size(collection_obj)
        else:
            return ObjectSize(size=0, flat_size=0, is_actual_size=False)

    def _remove_transaction_by_short_id(self, short_id):
        """
        Clean up short id mapping. Removes transaction contents and mapping if only one short id mapping.
        :param short_id: short id to clean up
        """
        if short_id in self._short_id_to_tx_hash:
            transaction_hash = self._short_id_to_tx_hash.pop(short_id)
            if transaction_hash in self._tx_hash_to_short_ids:
                short_ids = self._tx_hash_to_short_ids[transaction_hash]

                # Only clear mapping and txhash_to_contents if last SID assignment
                if len(short_ids) == 1:
                    del self._tx_hash_to_short_ids[transaction_hash]

                    if transaction_hash in self._tx_hash_to_contents:
                        self._total_tx_contents_size -= len(self._tx_hash_to_contents[transaction_hash])
                        del self._tx_hash_to_contents[transaction_hash]
                else:
                    short_ids.remove(short_id)

    def _memory_limit_clean_up(self):
        """
        Removes oldest transactions if total bytes consumed by transaction contents exceed memory limit
        """
        logger.debug("Transaction service exceeds memory limit for transaction contents. Limit: {}. Current size: {}."
                     .format(self._tx_content_memory_limit, self._total_tx_contents_size))
        removed_tx_count = 0

        while self._total_tx_contents_size > self._tx_content_memory_limit:
            self._tx_assignment_expire_queue.remove_oldest(remove_callback=self._remove_transaction_by_short_id)
            removed_tx_count += 1

        self._total_tx_removed_by_memory_limit += removed_tx_count
        logger.debug("Removed {} oldest transactions from transaction service cache. Size after clean up: {}".format(
            removed_tx_count, self._total_tx_contents_size))

    def _get_final_tx_confirmations_count(self):
        """
        Returns configuration value of number of block confirmations required before transaction can be removed
        """
        for blockchain_network in self.node.opts.blockchain_networks:
            if blockchain_network.network_num == self.network_num:
                return blockchain_network.final_tx_confirmations_count

        logger.warn("Tx service could not determine final confirmations count for network number {}. Using default {}."
                    .format(self.network_num, self.DEFAULT_FINAL_TX_CONFIRMATIONS_COUNT))

        return self.DEFAULT_FINAL_TX_CONFIRMATIONS_COUNT

    def _get_tx_contents_memory_limit(self):
        """
        Returns configuration value for memory limit for total transaction contents
        """
        if self.node.opts.transaction_pool_memory_limit is not None:
            # convert MB to bytes
            return self.node.opts.transaction_pool_memory_limit * 1024 * 1024

        for blockchain_network in self.node.opts.blockchain_networks:
            if blockchain_network.network_num == self.network_num:
                return blockchain_network.tx_contents_memory_limit_bytes

        logger.warn("Tx service could not determine transactions memory limit for network number {}. Using default {}."
                    .format(self.network_num, self.DEFAULT_TX_MEMORY_LIMIT))
        return self.DEFAULT_TX_MEMORY_LIMIT
