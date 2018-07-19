import heapq
import time

from bxcommon import constants
from bxcommon.utils import logger


class BlockRecoveryManager(object):
    """
    Logic to handle scenario when blocRoute gateway receives bloxRoute block message with transaction sid and hash
    that it is not aware of.
    """

    def __init__(self, alarm_queue):
        self.alarm_queue = alarm_queue

        self.block_hash_to_sids = {}
        self.block_hash_to_tx_hashes = {}
        self.block_hash_to_msg = {}

        self.block_add_times = []

        self.sid_to_block_hash = {}
        self.tx_hash_to_block_hash = {}

        self.recovered_msgs = []

        self.cleanup_scheduled = False

    def add_block_msg(self, msg, block_hash, unknown_tx_sids, unknown_tx_contents):
        logger.debug("Unknown tx: Tracking block with unknown txs. Block hash {0}".format(block_hash))

        self.block_hash_to_msg[block_hash] = msg

        heapq.heappush(self.block_add_times, (time.time(), block_hash))

        self.block_hash_to_sids[block_hash] = {}
        self.block_hash_to_tx_hashes[block_hash] = {}

        for sid in unknown_tx_sids:
            self.sid_to_block_hash[sid] = block_hash
            self.block_hash_to_sids[block_hash][sid] = True

        for tx_hash in unknown_tx_contents:
            self.tx_hash_to_block_hash[tx_hash] = block_hash
            self.block_hash_to_tx_hashes[block_hash][tx_hash] = True

        self._schedule_cleanup()

    def check_missing_sid(self, sid):
        if sid in self.sid_to_block_hash:
            logger.debug("Unknown tx: Received previously unknown tx sid {0}.".format(sid))

            block_hash = self.sid_to_block_hash[sid]

            if block_hash in self.block_hash_to_sids:
                if sid in self.block_hash_to_sids[block_hash]:
                    del self.block_hash_to_sids[block_hash][sid]

            del self.sid_to_block_hash[sid]

            self._check_if_recovered(block_hash)

    def check_missing_tx_hash(self, tx_hash):
        if tx_hash in self.tx_hash_to_block_hash:
            logger.debug("Unknown tx: Received previously unknown tx hash {0}.".format(tx_hash))

            block_hash = self.tx_hash_to_block_hash[tx_hash]

            if block_hash in self.block_hash_to_tx_hashes:
                if tx_hash in self.block_hash_to_tx_hashes[block_hash]:
                    del self.block_hash_to_tx_hashes[block_hash][tx_hash]

            del self.tx_hash_to_block_hash[tx_hash]

            self._check_if_recovered(block_hash)

    def cancel_recovery_for_block(self, block_hash):
        if block_hash in self.block_hash_to_msg:
            logger.debug("Unknown tx: Received block {0} from. Stop tracking block unknown txs.".format(block_hash))
            self._remove_not_recovered_msg(block_hash)

    def cleanup_old_messages(self, clean_up_time=None):
        logger.debug("Unknown tx: Running clean up task.")

        if clean_up_time is None:
            clean_up_time = time.time()

        while self.block_add_times and \
                clean_up_time - self.block_add_times[0][0] > constants.BROADCAST_MSG_EXPIRE_TIME:
            _, block_hash = heapq.heappop(self.block_add_times)

            self._remove_not_recovered_msg(block_hash)

        if self.block_hash_to_msg:
            return constants.BROADCAST_MSG_EXPIRE_TIME

        # disable clean up until receive the next msg with unknown tx
        self.cleanup_scheduled = False
        return 0

    def clean_up_recovered_messages(self):
        logger.debug("Unknown tx: Removing all of ready to retry messages. {0} messages."
                     .format(len(self.recovered_msgs)))
        del self.recovered_msgs[:]

    def _check_if_recovered(self, block_hash):
        if self._is_msg_recovered(block_hash):
            logger.debug("Unknown tx: Block {0} is ready for retry.".format(block_hash))
            msg = self.block_hash_to_msg[block_hash]
            self._remove_not_recovered_msg(block_hash)
            self.recovered_msgs.append(msg)

    def _is_msg_recovered(self, block_hash):
        return len(self.block_hash_to_sids[block_hash]) == 0 and len(self.block_hash_to_tx_hashes[block_hash]) == 0

    def _remove_not_recovered_msg(self, block_hash):
        if block_hash in self.block_hash_to_msg:
            logger.debug("Unknown tx: Removing block with hash {0}".format(block_hash))

            del self.block_hash_to_msg[block_hash]

            for sid in self.block_hash_to_sids[block_hash]:
                if sid in self.sid_to_block_hash:
                    del self.sid_to_block_hash[sid]

            del self.block_hash_to_sids[block_hash]

            for tx_hash in self.block_hash_to_tx_hashes[block_hash]:
                if tx_hash in self.tx_hash_to_block_hash:
                    del self.tx_hash_to_block_hash[tx_hash]

            del self.block_hash_to_tx_hashes[block_hash]

    def _schedule_cleanup(self):
        if not self.cleanup_scheduled and self.block_hash_to_msg:
            logger.debug("Unknown tx: Scheduling unknown tx blocks clean up in {0} seconds."
                         .format(constants.BROADCAST_MSG_EXPIRE_TIME))
            self.alarm_queue.register_alarm(constants.BROADCAST_MSG_EXPIRE_TIME, self.cleanup_old_messages)
            self.cleanup_scheduled = True
