import time

from bxcommon.utils import logger
from bxcommon.utils.expiration_queue import ExpirationQueue


# A manager for the transaction mappings
# We assume in this class that no more than MAX_ID unassigned services exist at a time
class TransactionService(object):
    # Size of a short id
    # If this is changed, make sure to change it in the TxAssignMessage
    SHORT_ID_SIZE = 4
    MAX_ID = 2 ** 32

    # The maximum amount of time that an ID is valid
    MAX_VALID_TIME = 600

    # Maximum amount of time we wait for the nodes to drop stale IDs
    MAX_SLOP_TIME = 120

    # is TransactionManager.MAX_VALID_TIME + TransactionManager.MAX_SLOP_TIME
    INITIAL_DELAY = 0

    NULL_TX = None

    def __init__(self, node):
        self.node = node

        # txhash is the longhash of the transaction, sid is the short ID for the transaction
        self.txhash_to_sid = {}
        # txid is the (unique) list of [time assigned, txhash]
        self.sid_to_txid = {}
        self.hash_to_contents = {}
        self.unassigned_hashes = set()
        self.tx_assignment_expire_queue = ExpirationQueue(TransactionService.MAX_VALID_TIME)
        self.tx_assign_alarm_scheduled = False

        self.relayed_txns = set()
        self.tx_relay_expire_queue = ExpirationQueue(TransactionService.MAX_VALID_TIME)

        self.prev_id = -1

        self.node.alarm_queue.register_alarm(TransactionService.INITIAL_DELAY, self.assign_initial_ids)

    def assign_initial_ids(self):
        assert self.prev_id == -1

        if self.unassigned_hashes:
            # FIXME there is no method _assign_tx_to_sid, change to assign_tx_to_sid and test
            raise RuntimeError("FIXME")

            # for tx_hash in self.unassigned_hashes:
            #     sid, tx_time = self.get_and_increment_id()
            #     self._assign_tx_to_sid(tx_hash, sid, tx_time)

        if self.tx_assignment_expire_queue:
            self.node.alarm_queue.register_alarm(TransactionService.MAX_VALID_TIME, self.expire_old_ids)
            self.tx_assign_alarm_scheduled = True
        self.unassigned_hashes = None

    def get_and_increment_id(self):
        self.prev_id += 1
        while self.prev_id in self.sid_to_txid:
            self.prev_id += 1

            if self.prev_id > TransactionService.MAX_ID:
                self.prev_id -= TransactionService.MAX_ID

        return self.prev_id, time.time()

    def expire_old_ids(self):
        self.tx_assignment_expire_queue.remove_expired(remove_callback=self.remove_tx_id)

        if self.tx_assignment_expire_queue:
            # Reschedule this function to be fired again after MAX_VALID_TIME seconds
            return TransactionService.MAX_VALID_TIME
        else:
            self.tx_assign_alarm_scheduled = False
            return 0

    def remove_tx_id(self, tx_id):
        tx_hash = tx_id[1]

        if tx_hash != TransactionService.NULL_TX:
            sid = self.txhash_to_sid[tx_hash]
            del self.txhash_to_sid[tx_hash]
            del self.sid_to_txid[sid]

    # Assigns the transaction to the given short id
    def assign_tx_to_sid(self, tx_hash, sid, tx_time):
        txid = [tx_time, tx_hash]

        self.txhash_to_sid[tx_hash] = sid
        self.sid_to_txid[sid] = txid

        self.tx_assignment_expire_queue.add(txid)

        if not self.tx_assign_alarm_scheduled:
            self.node.alarm_queue.register_alarm(TransactionService.MAX_VALID_TIME, self.expire_old_ids)
            self.tx_assign_alarm_scheduled = True

    def assign_tx_to_id(self, tx_hash):
        assert self.node.is_manager

        # Not done waiting for the initial services to come through
        if self.unassigned_hashes is not None:
            if tx_hash not in self.unassigned_hashes:
                self.unassigned_hashes.add(tx_hash)
            return -1
        elif tx_hash not in self.txhash_to_sid:
            logger.debug("XXX: Adding {0} to tx_hash mapping".format(tx_hash))
            sid, tx_time = self.get_and_increment_id()
            self.assign_tx_to_sid(tx_hash, sid, tx_time)
            return sid

    def get_txid(self, tx_hash):
        if tx_hash in self.txhash_to_sid:
            logger.debug("XXX: Found the tx_hash in my mappings!")
            return self.txhash_to_sid[tx_hash]

        return -1

    def get_tx_from_sid(self, sid):
        tx_hash = None

        if sid in self.sid_to_txid:
            tx_hash = self.sid_to_txid[sid][1]

            if tx_hash in self.hash_to_contents:
                return tx_hash, self.hash_to_contents[tx_hash]
            logger.debug("Looking for hash: " + repr(tx_hash))
            logger.debug("Could not find hash: " + repr(self.hash_to_contents.keys()[0:10]))

        return tx_hash, None

    def get_tx_details_from_sids(self, short_ids):
        """
        Finds details for transactions with short ids

        :param short_ids: array of transactions short ids
        :return: array of tuples (short id, tx hash, tx contents)
        """

        txs_details = []

        for short_id in short_ids:
            if short_id in self.node.tx_service.sid_to_txid:
                tx_hash = self.node.tx_service.sid_to_txid[short_id][1]

                if tx_hash in self.node.tx_service.hash_to_contents:
                    tx = self.node.tx_service.hash_to_contents[tx_hash]

                    txs_details.append((short_id, tx_hash, tx))
                else:
                    logger.debug(
                        "Block recovery: Contents of tx by short id {0} is unknown by server.".format(short_id))
            else:
                logger.debug("Block recovery: Short id {0} requested by client is unknown by server.".format(short_id))

        return txs_details

    # Returns True if
    def already_relayed(self, tx_hash):
        if tx_hash in self.relayed_txns:
            return True
        else:
            self.relayed_txns.add(tx_hash)
            self.tx_relay_expire_queue.add(tx_hash)
            self.node.alarm_queue.register_approx_alarm(2 * TransactionService.MAX_VALID_TIME,
                                                        TransactionService.MAX_VALID_TIME, self.cleanup_relayed)
            return False

    def cleanup_relayed(self):
        self.tx_relay_expire_queue.remove_expired(remove_callback=self.relayed_txns.remove)
        return 0
