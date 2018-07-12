import os
import time

from bxcommon.messages.broadcast_message import BroadcastMessage
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_alarm_queue import MockAlarmQueue
from bxcommon.transactions.missing_transactions_manager import MissingTransactionsManager

class MissingTransactionsManagerTest(AbstractTestCase):

    def setUp(self):
        self.alarm_queue = MockAlarmQueue()
        self.missing_tx_manager = MissingTransactionsManager(self.alarm_queue)
        self.msgs = []
        self.block_hashes = []
        self.unknown_tx_sids = []
        self.unknown_tx_hashes = []


    def test_on_broadcast_msg(self):
        self._add_broadcast_message()
        self._add_broadcast_message(1)
        self._add_broadcast_message(2)

    def test_remove_sid_if_missing(self):
        self._add_broadcast_message()

        sid = self.unknown_tx_sids[0][0]

        self.missing_tx_manager.remove_sid_if_missing(sid)

        self.assertTrue(len(self.missing_tx_manager.block_hash_to_sids[self.block_hashes[0]]) == 2)
        self.assertTrue(sid not in self.missing_tx_manager.sid_to_block_hash)

    def test_remove_tx_hash_if_missing(self):
        self._add_broadcast_message()

        tx_hash = self.unknown_tx_hashes[0][0]

        self.missing_tx_manager.remove_tx_hash_if_missing(tx_hash)

        self.assertTrue(len(self.missing_tx_manager.block_hash_to_tx_hashes[self.block_hashes[0]]) == 1)
        self.assertTrue(tx_hash not in self.missing_tx_manager.tx_hash_to_block_hash)

    def test_remove_block_if_missing(self):
        self._add_broadcast_message()

        self.missing_tx_manager.remove_block_if_missing(self.block_hashes[0])

        self.assertTrue(len(self.missing_tx_manager.block_hash_to_msg) == 0)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_sids) == 0)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_tx_hashes) == 0)

        self.assertTrue(len(self.missing_tx_manager.sid_to_block_hash) == 0)
        self.assertTrue(len(self.missing_tx_manager.tx_hash_to_block_hash) == 0)

    def test_msgs_ready_for_retry__sids_arrive_first(self):
        self._add_broadcast_message()

        for sid in self.unknown_tx_sids[0]:
            self.missing_tx_manager.remove_sid_if_missing(sid)


        for tx_hash in self.unknown_tx_hashes[0]:
            self.missing_tx_manager.remove_tx_hash_if_missing(tx_hash)

        self.assertTrue(len(self.missing_tx_manager.block_hash_to_msg) == 0)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_sids) == 0)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_tx_hashes) == 0)

        self.assertTrue(len(self.missing_tx_manager.sid_to_block_hash) == 0)
        self.assertTrue(len(self.missing_tx_manager.tx_hash_to_block_hash) == 0)

        self.assertTrue(len(self.missing_tx_manager.msgs_ready_for_retry) == 1)
        self.assertTrue(self.missing_tx_manager.msgs_ready_for_retry[0] == self.msgs[0])

    def test_msgs_ready_for_retry__tx_contents_arrive_first(self):
        self._add_broadcast_message()

        for sid in self.unknown_tx_sids[0]:
            self.missing_tx_manager.remove_sid_if_missing(sid)

        for tx_hash in self.unknown_tx_hashes[0]:
            self.missing_tx_manager.remove_tx_hash_if_missing(tx_hash)

        self.assertTrue(len(self.missing_tx_manager.block_hash_to_msg) == 0)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_sids) == 0)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_tx_hashes) == 0)

        self.assertTrue(len(self.missing_tx_manager.sid_to_block_hash) == 0)
        self.assertTrue(len(self.missing_tx_manager.tx_hash_to_block_hash) == 0)

        self.assertTrue(len(self.missing_tx_manager.msgs_ready_for_retry) == 1)
        self.assertTrue(self.missing_tx_manager.msgs_ready_for_retry[0] == self.msgs[0])


    def test_clean_up_old_messages__single_message(self):
        self.assertFalse(self.missing_tx_manager.cleanup_scheduled)
        self.assertTrue(len(self.alarm_queue.alarms) == 0)

        self._add_broadcast_message()

        self.assertTrue(len(self.alarm_queue.alarms) == 1)
        self.assertTrue(self.alarm_queue.alarms[0][0] == MissingTransactionsManager.MAX_VALID_TIME)
        self.assertTrue(self.alarm_queue.alarms[0][1] == self.missing_tx_manager.cleanup_old_messages)

        self.assertTrue(self.missing_tx_manager.cleanup_scheduled)

        self.missing_tx_manager.cleanup_old_messages(time.time() + 30)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_msg) == 1)
        self.assertTrue(self.missing_tx_manager.cleanup_scheduled)

        self.missing_tx_manager.cleanup_old_messages(time.time() + 61)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_msg) == 0)
        self.assertFalse(self.missing_tx_manager.cleanup_scheduled)

    def test_clean_up_ready_for_retry_messages(self):
        self.assertTrue(len(self.missing_tx_manager.msgs_ready_for_retry) == 0)

        self.missing_tx_manager.msgs_ready_for_retry.append(self._create_broadcast_msg())
        self.missing_tx_manager.msgs_ready_for_retry.append(self._create_broadcast_msg())
        self.missing_tx_manager.msgs_ready_for_retry.append(self._create_broadcast_msg())

        self.assertTrue(len(self.missing_tx_manager.msgs_ready_for_retry) == 3)

        self.missing_tx_manager.clean_up_ready_for_retry_messages()

        self.assertTrue(len(self.missing_tx_manager.msgs_ready_for_retry) == 0)

    def test_clean_up_old_messages__multiple_messages(self):
        self.assertFalse(self.missing_tx_manager.cleanup_scheduled)
        self.assertTrue(len(self.alarm_queue.alarms) == 0)

        self._add_broadcast_message()
        time.sleep(2)
        self._add_broadcast_message(1)

        self.assertTrue(len(self.alarm_queue.alarms) == 1)
        self.assertTrue(self.alarm_queue.alarms[0][0] == MissingTransactionsManager.MAX_VALID_TIME)
        self.assertTrue(self.alarm_queue.alarms[0][1] == self.missing_tx_manager.cleanup_old_messages)

        self.missing_tx_manager.cleanup_old_messages(time.time() + 30)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_msg) == 2)

        self.missing_tx_manager.cleanup_old_messages(time.time() + 58)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_msg) == 1)

        self.assertTrue(self.missing_tx_manager.cleanup_scheduled)

        #verify that the latest block left
        self.assertTrue(self.block_hashes[0] not in self.missing_tx_manager.block_hash_to_msg)
        self.assertTrue(self.block_hashes[1] in self.missing_tx_manager.block_hash_to_msg)
        self.assertTrue(self.missing_tx_manager.cleanup_scheduled)

    def _add_broadcast_message(self, existing_msgs_count=0):
        self.block_hashes.append(os.urandom(32))

        self.msgs.append(self._create_broadcast_msg())

        sid_base = existing_msgs_count * 10
        self.unknown_tx_sids.append([sid_base + 1, sid_base + 2, sid_base + 3])
        self.unknown_tx_hashes.append([os.urandom(32), os.urandom(32)])

        self.assertTrue(len(self.missing_tx_manager.block_hash_to_msg) == existing_msgs_count)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_sids) == existing_msgs_count)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_tx_hashes) == existing_msgs_count)

        self.assertTrue(len(self.missing_tx_manager.block_add_times) == existing_msgs_count)

        self.assertTrue(len(self.missing_tx_manager.sid_to_block_hash) == existing_msgs_count * 3)
        self.assertTrue(len(self.missing_tx_manager.tx_hash_to_block_hash) == existing_msgs_count * 2)

        self.missing_tx_manager \
            .add_msg_with_missing_txs(self.msgs[-1], self.block_hashes[-1], self.unknown_tx_sids[-1][:], self.unknown_tx_hashes[-1][:])

        self.assertTrue(len(self.missing_tx_manager.block_hash_to_msg) == existing_msgs_count + 1)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_sids) == existing_msgs_count + 1)
        self.assertTrue(len(self.missing_tx_manager.block_hash_to_tx_hashes) == existing_msgs_count + 1)

        self.assertTrue(len(self.missing_tx_manager.block_add_times) == existing_msgs_count + 1)

        self.assertTrue(len(self.missing_tx_manager.sid_to_block_hash) == existing_msgs_count * 3 + 3)
        self.assertTrue(len(self.missing_tx_manager.tx_hash_to_block_hash) == existing_msgs_count * 2 + 2)

        self.assertTrue(self.missing_tx_manager.block_hash_to_msg[self.block_hashes[-1]] == self.msgs[-1])
        self.assertTrue(self.missing_tx_manager.block_hash_to_sids[self.block_hashes[-1]] == self.unknown_tx_sids[-1])
        self.assertTrue(self.missing_tx_manager.block_hash_to_tx_hashes[self.block_hashes[-1]] == self.unknown_tx_hashes[-1])

        for sid in self.unknown_tx_sids[-1]:
            self.assertTrue(self.missing_tx_manager.sid_to_block_hash[sid] == self.block_hashes[-1])

        for tx_hash in self.unknown_tx_hashes[-1]:
            self.assertTrue(self.missing_tx_manager.tx_hash_to_block_hash[tx_hash] == self.block_hashes[-1])

    def _create_broadcast_msg(self):
        message_buffer = bytearray()
        message_buffer.extend(os.urandom(500))
        return BroadcastMessage(buf=message_buffer)
