from bxcommon.messages.get_txs_details_message import GetTxsDetailsMessage
from bxcommon.test_utils.abstract_test_case import AbstractTestCase

class GetTxsDetailsMessageTests(AbstractTestCase):

    def test_get_txs_with_short_ids_message(self):
        short_ids = [23, 99, 192, 1089, 3000500]

        msg = GetTxsDetailsMessage(short_ids=short_ids)

        msg_bytes = msg.rawbytes()

        self.assertTrue(msg_bytes)

        parsed_msg = GetTxsDetailsMessage(buf=msg_bytes)

        self.assertTrue(parsed_msg)

        parsed_short_ids = parsed_msg.short_ids()

        self.assertTrue(len(parsed_short_ids) == len(short_ids))

        for index in range(len(short_ids)):
            self.assertTrue(parsed_short_ids[index] == short_ids[index])