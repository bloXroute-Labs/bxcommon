from typing import List, Optional

from bxcommon import constants
from bxcommon.messages.bloxroute import transactions_info_serializer
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.models.transaction_info import TransactionInfo
from bxutils import logging
from bxutils.logging.log_level import LogLevel

logger = logging.get_logger(__name__)


class TxsMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.TRANSACTIONS
    """
    Message with tx details. Reply to GetTxsMessage.
    """

    # pyre-fixme[9]: buf has type `bytearray`; used as `None`.
    def __init__(self, txs: Optional[List[TransactionInfo]] = None, buf: bytearray = None) -> None:

        """
        Constructor. Expects list of transaction details or message bytes.

        :param txs: tuple with 3 values (tx short id, tx hash, tx contents)
        :param buf: message bytes
        """

        if buf is None:
            assert txs is not None
            buf = self._txs_to_bytes(txs)

        super(TxsMessage, self).__init__(self.MESSAGE_TYPE, len(buf) - self.HEADER_LENGTH, buf)
        self._txs = None

    def log_level(self):
        return LogLevel.DEBUG

    def get_txs(self) -> List[TransactionInfo]:
        if self._txs is None:
            self._parse()

        assert self._txs is not None
        # pyre-fixme[7]: Expected `List[TransactionInfo]` but got `None`.
        return self._txs

    def _txs_to_bytes(self, txs_details: List[TransactionInfo]):
        # msg_size = HDR_COMMON_OFF + tx count + (sid + hash + tx size) of each tx
        msg_size = (
            self.HEADER_LENGTH
            + transactions_info_serializer.get_serialized_length(txs_details)
            + constants.CONTROL_FLAGS_LEN
        )

        buf = bytearray(msg_size)
        off = self.HEADER_LENGTH

        transactions_info_serializer.serialize_transactions_info_to_buffer(txs_details, buf, off)

        return buf

    def _parse(self):
        self._txs, _ = transactions_info_serializer.deserialize_transactions_info_from_buffer(
            self.buf,
            self.HEADER_LENGTH
        )

    def __repr__(self):
        return "TxsMessage<num_txs: {}>".format(len(self.get_txs()))
