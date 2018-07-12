import unittest

from bxcommon import constants
from bxcommon.utils import logger
from bxcommon.utils.object_hash import ObjectHash
from bxcommon.messages.txs_details_message import TxsDetailsMessage
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils import helpers

class TxsDetailsMessageTests(AbstractTestCase):

    def test_txs_with_short_ids_message(self):
        txs_info = []
        txs_info.append((10, ObjectHash(helpers.generate_bytearray(32)), helpers.generate_bytearray(251)))
        txs_info.append((23, ObjectHash(helpers.generate_bytearray(32)), helpers.generate_bytearray(303)))
        txs_info.append((74, ObjectHash(helpers.generate_bytearray(32)), helpers.generate_bytearray(567)))

        msg = TxsDetailsMessage(txs_info=txs_info)

        msg_bytes = msg.rawbytes()

        self.assertTrue(msg_bytes)

        parsed_msg = TxsDetailsMessage(buf=msg_bytes)

        self.assertTrue(parsed_msg)

        parsed_txs_info = parsed_msg.txs_info()

        self.assertEqual(len(parsed_txs_info), len(txs_info))

        for index in range(len(txs_info)):
            self.assertEqual(parsed_txs_info[index][0], txs_info[index][0])
            self.assertEqual(parsed_txs_info[index][1], txs_info[index][1])
            self.assertEqual(parsed_txs_info[index][2], txs_info[index][2])
