from collections import deque

from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.models.transaction_info import TransactionInfo
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.object_hash import Sha256Hash


class TxsMessageTests(AbstractTestCase):

    def test_txs_with_short_ids_message(self):
        txs_info = [
            TransactionInfo(Sha256Hash(helpers.generate_bytearray(32)), helpers.generate_bytearray(200), 111),
            TransactionInfo(Sha256Hash(helpers.generate_bytearray(32)), helpers.generate_bytearray(300), 222),
            TransactionInfo(Sha256Hash(helpers.generate_bytearray(32)), helpers.generate_bytearray(400), 333)
        ]

        msg = TxsMessage(txs=txs_info)

        msg_bytes = msg.rawbytes()

        self.assertTrue(msg_bytes)

        parsed_msg = TxsMessage(buf=msg_bytes)

        self.assertTrue(parsed_msg)

        parsed_txs_info = parsed_msg.get_txs()

        self.assertEqual(len(parsed_txs_info), len(txs_info))

        for index in range(len(txs_info)):
            self.assertEqual(parsed_txs_info[index].short_id, txs_info[index].short_id)
            self.assertEqual(parsed_txs_info[index].contents, txs_info[index].contents)
            self.assertEqual(parsed_txs_info[index].hash, txs_info[index].hash)
