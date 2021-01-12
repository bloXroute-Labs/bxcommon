from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.models.transaction_flag import TransactionFlag
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase


class TxMessageTest(AbstractTestCase):
    def test_set_transaction_flag(self):
        tx_message = TxMessage(
            helpers.generate_object_hash(),
            1,
            "",
            tx_val=helpers.generate_bytearray(250),
            transaction_flag=TransactionFlag.PAID_TX
        )
        tx_message.set_transaction_flag(
            TransactionFlag.PAID_TX
            | TransactionFlag.CEN_ENABLED
            | TransactionFlag.LOCAL_REGION
            | TransactionFlag.TBD_2
        )
        reserialized_message = self._serialize_deserialize_message(tx_message)
        self.assertTrue(
            TransactionFlag.CEN_ENABLED in reserialized_message.transaction_flag()
        )
        self.assertTrue(
            TransactionFlag.LOCAL_REGION in reserialized_message.transaction_flag()
        )
        self.assertTrue(
            TransactionFlag.TBD_2 in reserialized_message.transaction_flag()
        )

    def _serialize_deserialize_message(
        self, tx_message: TxMessage
    ) -> TxMessage:
        tx_message_bytes = tx_message.rawbytes()
        reserialized_tx_message = AbstractInternalMessage.initialize_class(
            TxMessage,
            tx_message_bytes,
            (TxMessage.MESSAGE_TYPE, tx_message.payload_len())
        )
        self.assertEqual(
            tx_message_bytes,
            reserialized_tx_message.rawbytes()
        )
        return reserialized_tx_message