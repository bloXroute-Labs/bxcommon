from collections import defaultdict, deque

from pympler import asizeof

from bxcommon import constants
from bxcommon.utils import logger
from bxcommon.utils.expiration_queue import ExpirationQueue
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
    txhash_to_sids: mapping of transaction long hashes to (potentially multiple) short ids
    sid_to_txhash: mapping of short id to transaction long hashes
    txhash_to_contents: mapping of transaction long hashes to transaction contents
    tx_assignment_expire_queue: expiration time of short ids
    tx_assign_alarm_scheduled: if an alarm to expire a batch of short ids is currently active
    network_num: network number that current transaction service serves
    """

    MAX_ID = 2 ** 32
    SHORT_ID_SIZE = 4
    DEFAULT_FINAL_TX_CONFIRMATIONS_COUNT = 24

    def __init__(self, node, network_num):
        self.node = node
        self.txhash_to_sids = defaultdict(set)
        self.sid_to_txhash = {}
        self.txhash_to_contents = {}
        self.tx_assignment_expire_queue = ExpirationQueue(node.opts.sid_expire_time)
        self.tx_assign_alarm_scheduled = False
        self.network_num = network_num

        self.final_tx_confirmations_count = self._get_final_tx_confirmations_count()

        # deque of short ids in blocks in the order they are received
        self.short_ids_seen_in_block = deque()

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
        self.txhash_to_sids[transaction_hash].add(short_id)
        self.sid_to_txhash[short_id] = transaction_hash
        self.tx_assignment_expire_queue.add(short_id)

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
        if transaction_hash in self.txhash_to_sids:
            return self.txhash_to_sids[transaction_hash]
        else:
            return {constants.NULL_TX_SID}

    def get_transaction(self, short_id):
        """
        Fetches transaction info for a given short id.
        Results might be None.
        :param short_id:
        :return: transaction hash, transaction contents.
        """
        if short_id in self.sid_to_txhash:
            transaction_hash = self.sid_to_txhash[short_id]
            if transaction_hash in self.txhash_to_contents:
                return transaction_hash, self.txhash_to_contents[transaction_hash]
            else:
                return transaction_hash, None
        else:
            return None, None

    def get_transactions(self, short_ids):
        """
        Fetches all transaction info for a set of short ids.
        Short ids without a transaction entry will be omitted.
        :param short_ids: list of short ids
        :return: list of (transaction hash, transaction contents)
        """
        transactions = []
        for short_id in short_ids:
            if short_id in self.sid_to_txhash:
                transaction_hash = self.sid_to_txhash[short_id]
                if transaction_hash in self.txhash_to_contents:
                    tx = self.txhash_to_contents[transaction_hash]
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
        logger.info("Expiring old short id assignments. Total entries: {}".format(len(self.tx_assignment_expire_queue)))
        self.tx_assignment_expire_queue.remove_expired(remove_callback=self._remove_transaction_by_short_id)
        logger.info(
            "Finished cleaning up short ids. Entries remaining: {}".format(len(self.tx_assignment_expire_queue)))
        if len(self.tx_assignment_expire_queue) > 0:
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

        self.short_ids_seen_in_block.append(short_ids)

        if len(self.short_ids_seen_in_block) > self.final_tx_confirmations_count:

            final_short_ids = self.short_ids_seen_in_block.popleft()

            for short_id in final_short_ids:
                self._remove_transaction_by_short_id(short_id)

    def _remove_transaction_by_short_id(self, short_id):
        """
        Clean up short id mapping. Removes transaction contents and mapping if only one short id mapping.
        :param short_id: short id to clean up
        """
        if short_id in self.sid_to_txhash:
            transaction_hash = self.sid_to_txhash.pop(short_id)
            if transaction_hash in self.txhash_to_sids:
                short_ids = self.txhash_to_sids[transaction_hash]

                # Only clear mapping and txhash_to_contents if last SID assignment
                if len(short_ids) == 1:
                    del self.txhash_to_sids[transaction_hash]
                    if transaction_hash in self.txhash_to_contents:
                        del self.txhash_to_contents[transaction_hash]
                else:
                    short_ids.remove(short_id)

    def log_tx_service_mem_stats(self):
        """
        Logs transactions service memory statistics
        """

        class_name = self.__class__.__name__
        hooks.add_obj_mem_stats(
            class_name,
            self.network_num,
            self.txhash_to_sids,
            "txhash_to_sids",
            self.get_collection_mem_stats(self.txhash_to_sids))

        hooks.add_obj_mem_stats(
            class_name,
            self.network_num,
            self.txhash_to_contents,
            "hash_to_contents",
            self.get_collection_mem_stats(self.txhash_to_contents))

        hooks.add_obj_mem_stats(
            class_name,
            self.network_num,
            self.sid_to_txhash,
            "sid_to_txid",
            self.get_collection_mem_stats(self.sid_to_txhash))

        hooks.add_obj_mem_stats(
            class_name,
            self.network_num,
            self.short_ids_seen_in_block,
            "short_ids_seen_in_block",
            self.get_collection_mem_stats(self.short_ids_seen_in_block))

    def get_tx_service_aggregate_stats(self):
        """
        Returns dictionary with aggregated statistics of transactions service

        :return: dictionary with aggregated statistics
        """

        if len(self.tx_assignment_expire_queue.queue) > 0:
            oldest_transaction_date = self.tx_assignment_expire_queue.queue[0][0]
        else:
            oldest_transaction_date = 0
        return dict(
            short_id_mapping_count_gauge=len(self.sid_to_txhash),
            unique_transaction_content_gauge=len(self.txhash_to_contents),
            oldest_transaction_date=oldest_transaction_date
        )

    def get_collection_mem_stats(self, collection_obj, ):
        if self.node.opts.stats_calculate_actual_size:
            obj_size = asizeof.asized(collection_obj)
            return (obj_size.size, obj_size.flat, True)
        else:
            return (0, 0, False)

    def _get_final_tx_confirmations_count(self):
        for blockchain_network in self.node.opts.blockchain_networks:
            if blockchain_network.network_num == self.network_num:
                return blockchain_network.final_tx_confirmations_count

        logger.warn("Tx service could not determine final confirmations count for network number {}. Using default {}."
                    .format(self.network_num, self.DEFAULT_FINAL_TX_CONFIRMATIONS_COUNT))

        return self.DEFAULT_FINAL_TX_CONFIRMATIONS_COUNT
