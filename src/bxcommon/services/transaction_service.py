from collections import defaultdict

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
    MAX_SLOP_TIME: max amount of time we wait for nodes to drop stale short ids


    Attributes
    ----------
    node: reference to node holding transaction service reference
    txhash_to_sids: mapping of transaction long hashes to (potentially multiple) short ids
    sid_to_txhash: mapping of short id to transaction long hashes
    txhash_to_contents: mapping of transaction long hashes to transaction contents
    tx_assignment_expire_queue: expiration time of short ids
    tx_assign_alarm_scheduled: if an alarm to expire a batch of short ids is currently active
    """

    MAX_ID = 2 ** 32
    SHORT_ID_SIZE = 4
    MAX_SLOP_TIME = 120

    def __init__(self, node):
        self.node = node
        self.txhash_to_sids = defaultdict(set)
        self.sid_to_txhash = {}
        self.txhash_to_contents = {}
        self.tx_assignment_expire_queue = ExpirationQueue(node.opts.sid_expire_time)
        self.tx_assign_alarm_scheduled = False

    def assign_short_id(self, transaction_hash, short_id):
        """
        Adds short id mapping for transaction and schedules an alarm to cleanup entry on expiration.
        :param transaction_hash: transaction long hash
        :param short_id: short id to be mapped to transaction
        """
        if short_id == constants.NULL_TX_SID:
            logger.warn("Attempt to assign null SID to transaction hash {}. Ignoring.".format(transaction_hash))
            return
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
                    logger.warn("Short id {} was requested but is unknown.".format(short_id))
            else:
                logger.warn("Short id {} was requested but is unknown.".format(short_id))

        return transactions

    def expire_old_assignments(self):
        """
        Clean up expired short ids.
        """
        logger.info("Expiring old short id assignments. Total entries: {}".format(len(self.tx_assignment_expire_queue)))
        self.tx_assignment_expire_queue.remove_expired(remove_callback=self._expire_assignment)
        logger.info("Finished cleaning up short ids. Entries remaining: {}".format(len(self.tx_assignment_expire_queue)))
        if len(self.tx_assignment_expire_queue) > 0:
            return self.node.opts.sid_expire_time
        else:
            self.tx_assign_alarm_scheduled = False
            return 0

    def _expire_assignment(self, short_id):
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

    def log_tx_service_mem_stats(self, network_num=0):
        class_name = self.__class__.__name__
        hooks.add_obj_mem_stats(
            class_name,
            network_num,
            self.txhash_to_sids,
            "txhash_to_sid",
            asizeof.asized(self.txhash_to_sids))

        hooks.add_obj_mem_stats(
            class_name,
            network_num,
            self.txhash_to_contents,
            "hash_to_contents",
            asizeof.asized(self.txhash_to_contents))

        hooks.add_obj_mem_stats(
            class_name,
            network_num,
            self.sid_to_txhash,
            "sid_to_txid",
            asizeof.asized(self.sid_to_txhash))
