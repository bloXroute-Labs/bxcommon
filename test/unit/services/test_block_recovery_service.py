import os
import time

from mock import MagicMock

from bxcommon import constants
from bxcommon.messages.broadcast_message import BroadcastMessage
from bxcommon.services.block_recovery_service import BlockRecoveryService
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_alarm_queue import MockAlarmQueue


class BlockRecoveryManagerTest(AbstractTestCase):

    def setUp(self):
        self.alarm_queue = MockAlarmQueue()
        self.block_recovery_service = BlockRecoveryService(self.alarm_queue)
        self.msgs = []
        self.block_hashes = []
        self.unknown_tx_sids = []
        self.unknown_tx_hashes = []

    def test_add_block_msg(self):
        self._add_broadcast_message()
        self._add_broadcast_message(1)
        self._add_broadcast_message(2)

    def test_check_missing_sid(self):
        self._add_broadcast_message()

        sid = self.unknown_tx_sids[0][0]

        self.block_recovery_service.check_missing_sid(sid)

        self.assertEqual(len(self.block_recovery_service.block_hash_to_sids[self.block_hashes[0]]), 2)
        self.assertNotIn(sid, self.block_recovery_service.sid_to_block_hash)

    def test_check_missing_tx_hash(self):
        self._add_broadcast_message()

        tx_hash = self.unknown_tx_hashes[0][0]

        self.block_recovery_service.check_missing_tx_hash(tx_hash)

        self.assertEqual(len(self.block_recovery_service.block_hash_to_tx_hashes[self.block_hashes[0]]), 1)
        self.assertNotIn(tx_hash, self.block_recovery_service.tx_hash_to_block_hash)

    def test_cancel_recovery_for_block(self):
        self._add_broadcast_message()

        self.block_recovery_service.cancel_recovery_for_block(self.block_hashes[0])

        self.assertEqual(len(self.block_recovery_service.block_hash_to_msg), 0)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_sids), 0)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_tx_hashes), 0)

        self.assertEqual(len(self.block_recovery_service.sid_to_block_hash), 0)
        self.assertEqual(len(self.block_recovery_service.tx_hash_to_block_hash), 0)

    def test_recovered_msgs__sids_arrive_first(self):
        self._add_broadcast_message()

        # Missing sids arrive first
        for sid in self.unknown_tx_sids[0]:
            self.block_recovery_service.check_missing_sid(sid)

        # Then tx hashes arrive
        for tx_hash in self.unknown_tx_hashes[0]:
            self.block_recovery_service.check_missing_tx_hash(tx_hash)

        self.assertEqual(len(self.block_recovery_service.block_hash_to_msg), 0)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_sids), 0)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_tx_hashes), 0)

        self.assertEqual(len(self.block_recovery_service.sid_to_block_hash), 0)
        self.assertEqual(len(self.block_recovery_service.tx_hash_to_block_hash), 0)

        self.assertEqual(len(self.block_recovery_service.recovered_msgs), 1)
        self.assertEqual(self.block_recovery_service.recovered_msgs[0], self.msgs[0])

    def test_recovered_msgs__tx_contents_arrive_first(self):
        self._add_broadcast_message()

        # Missing tx hashes arrive first
        for tx_hash in self.unknown_tx_hashes[0]:
            self.block_recovery_service.check_missing_tx_hash(tx_hash)

        # Then missing sids arrive
        for sid in self.unknown_tx_sids[0]:
            self.block_recovery_service.check_missing_sid(sid)

        # Verify that no txs all blocks missing
        self.assertEqual(len(self.block_recovery_service.block_hash_to_msg), 0)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_sids), 0)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_tx_hashes), 0)
        self.assertEqual(len(self.block_recovery_service.sid_to_block_hash), 0)
        self.assertEqual(len(self.block_recovery_service.tx_hash_to_block_hash), 0)

        # Verify that message is ready for retry
        self.assertEqual(len(self.block_recovery_service.recovered_msgs), 1)
        self.assertEqual(self.block_recovery_service.recovered_msgs[0], self.msgs[0])

    def test_clean_up_old_messages__single_message(self):
        self.assertFalse(self.block_recovery_service.cleanup_scheduled)
        self.assertEqual(len(self.alarm_queue.alarms), 0)

        # Adding missing message
        self._add_broadcast_message()

        # Verify that clean up is scheduled
        self.assertEqual(len(self.alarm_queue.alarms), 1)
        self.assertEqual(self.alarm_queue.alarms[0][0], constants.MISSING_BLOCK_EXPIRE_TIME)
        self.assertEqual(self.alarm_queue.alarms[0][1], self.block_recovery_service.cleanup_old_messages)

        self.assertTrue(self.block_recovery_service.cleanup_scheduled)

        # Run clean up before message expires and check that it is still there
        self.block_recovery_service.cleanup_old_messages(time.time() + constants.MISSING_BLOCK_EXPIRE_TIME / 2)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_msg), 1)
        self.assertTrue(self.block_recovery_service.cleanup_scheduled)

        # Run clean up after message expires and check that it is removed
        self.block_recovery_service.cleanup_old_messages(time.time() + constants.MISSING_BLOCK_EXPIRE_TIME + 1)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_msg), 0)
        self.assertFalse(self.block_recovery_service.cleanup_scheduled)

    def test_clean_up_recovered_messages(self):
        self.assertTrue(len(self.block_recovery_service.recovered_msgs) == 0)

        # Adding ready to retry messages
        self.block_recovery_service.recovered_msgs.append(self._create_broadcast_msg())
        self.block_recovery_service.recovered_msgs.append(self._create_broadcast_msg())
        self.block_recovery_service.recovered_msgs.append(self._create_broadcast_msg())

        self.assertEqual(len(self.block_recovery_service.recovered_msgs), 3)

        # Removing ready to retry messages and verify that they are removed
        self.block_recovery_service.clean_up_recovered_messages()

        self.assertEqual(len(self.block_recovery_service.recovered_msgs), 0)

    def test_clean_up_old_messages__multiple_messages(self):
        self.assertFalse(self.block_recovery_service.cleanup_scheduled)
        self.assertEqual(len(self.alarm_queue.alarms), 0)

        # Adding to messages with 2 seconds difference between them
        self._add_broadcast_message()
        time.time = MagicMock(return_value=time.time() + 3)
        self._add_broadcast_message(1)

        # Verify that clean up scheduled
        self.assertEqual(len(self.alarm_queue.alarms), 1)
        self.assertEqual(self.alarm_queue.alarms[0][0], constants.MISSING_BLOCK_EXPIRE_TIME)
        self.assertEqual(self.alarm_queue.alarms[0][1], self.block_recovery_service.cleanup_old_messages)

        # Verify that both messages are there before the first one expires
        self.block_recovery_service.cleanup_old_messages(time.time() + constants.MISSING_BLOCK_EXPIRE_TIME / 2)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_msg), 2)

        # Verify that first message is remove and the second left 2 seconds before second message expires
        self.block_recovery_service.cleanup_old_messages(time.time() + constants.MISSING_BLOCK_EXPIRE_TIME - 2)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_msg), 1)

        self.assertTrue(self.block_recovery_service.cleanup_scheduled)

        # verify that the latest block left
        self.assertNotIn(self.block_hashes[0], self.block_recovery_service.block_hash_to_msg)
        self.assertIn(self.block_hashes[1], self.block_recovery_service.block_hash_to_msg)
        self.assertTrue(self.block_recovery_service.cleanup_scheduled)

    def _add_broadcast_message(self, existing_msgs_count=0):
        self.block_hashes.append(os.urandom(32))

        self.msgs.append(self._create_broadcast_msg())

        sid_base = existing_msgs_count * 10
        self.unknown_tx_sids.append([sid_base + 1, sid_base + 2, sid_base + 3])
        self.unknown_tx_hashes.append([os.urandom(32), os.urandom(32)])

        self.assertEqual(len(self.block_recovery_service.block_hash_to_msg), existing_msgs_count)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_sids), existing_msgs_count)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_tx_hashes), existing_msgs_count)

        self.assertEqual(len(self.block_recovery_service.blocks_expiration_queue), existing_msgs_count)

        self.assertEqual(len(self.block_recovery_service.sid_to_block_hash), existing_msgs_count * 3)
        self.assertEqual(len(self.block_recovery_service.tx_hash_to_block_hash), existing_msgs_count * 2)

        self.block_recovery_service \
            .add_block_msg(self.msgs[-1], self.block_hashes[-1], self.unknown_tx_sids[-1][:],
                           self.unknown_tx_hashes[-1][:])

        self.assertEqual(len(self.block_recovery_service.block_hash_to_msg), existing_msgs_count + 1)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_sids), existing_msgs_count + 1)
        self.assertEqual(len(self.block_recovery_service.block_hash_to_tx_hashes), existing_msgs_count + 1)

        self.assertEqual(len(self.block_recovery_service.blocks_expiration_queue), existing_msgs_count + 1)

        self.assertEqual(len(self.block_recovery_service.sid_to_block_hash), existing_msgs_count * 3 + 3)
        self.assertEqual(len(self.block_recovery_service.tx_hash_to_block_hash), existing_msgs_count * 2 + 2)

        self.assertEqual(self.block_recovery_service.block_hash_to_msg[self.block_hashes[-1]], self.msgs[-1])

        self.assertEqual(self.block_recovery_service.block_hash_to_sids[self.block_hashes[-1]],
                         set(self.unknown_tx_sids[-1]))
        self.assertEqual(self.block_recovery_service.block_hash_to_tx_hashes[self.block_hashes[-1]],
                         set(self.unknown_tx_hashes[-1]))

        for sid in self.unknown_tx_sids[-1]:
            self.assertEqual(self.block_recovery_service.sid_to_block_hash[sid], self.block_hashes[-1])

        for tx_hash in self.unknown_tx_hashes[-1]:
            self.assertEqual(self.block_recovery_service.tx_hash_to_block_hash[tx_hash], self.block_hashes[-1])

    def _create_broadcast_msg(self):
        message_buffer = bytearray()
        message_buffer.extend(os.urandom(500))
        return BroadcastMessage(buf=message_buffer)
