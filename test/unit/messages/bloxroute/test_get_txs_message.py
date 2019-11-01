from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage


class GetTxsMessageTests(AbstractTestCase):

    def test_get_txs_with_short_ids_message(self):
        short_ids = [23, 99, 192, 1089, 3000500]

        msg = GetTxsMessage(short_ids=short_ids)

        msg_bytes = msg.rawbytes()

        self.assertTrue(msg_bytes)

        parsed_msg = GetTxsMessage(buf=msg_bytes)

        self.assertTrue(parsed_msg)

        parsed_short_ids = parsed_msg.get_short_ids()

        self.assertEqual(len(parsed_short_ids), len(short_ids))

        for index in range(len(short_ids)):
            self.assertEqual(parsed_short_ids[index], short_ids[index])
