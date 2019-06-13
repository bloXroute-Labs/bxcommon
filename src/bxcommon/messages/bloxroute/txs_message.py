import struct
from typing import List, Optional

import bxcommon.utils.crypto
from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.message import Message
from bxcommon.models.transaction_info import TransactionInfo
from bxcommon.utils import logger
from bxcommon.utils.log_level import LogLevel
from bxcommon.utils.object_hash import Sha256Hash


class TxsMessage(Message):
    MESSAGE_TYPE = BloxrouteMessageType.TRANSACTIONS
    """
    Message with tx details. Reply to GetTxsMessage.
    """

    def __init__(self, txs: Optional[List[TransactionInfo]] = None, buf: bytearray = None):

        """
        Constructor. Expects list of transaction details or message bytes.

        :param txs: tuple with 3 values (tx short id, tx hash, tx contents)
        :param buf: message bytes
        """

        if buf is None:
            buf = self._txs_to_bytes(txs)
            super(TxsMessage, self).__init__(self.MESSAGE_TYPE, len(buf) - constants.HDR_COMMON_OFF, buf)
        else:
            if isinstance(buf, str):
                raise TypeError("Buffer can't be string")

            self.buf = buf
            self._memoryview = memoryview(self.buf)

        self._txs = None

    def log_level(self):
        return LogLevel.INFO

    def get_txs(self) -> List[TransactionInfo]:
        if self._txs is None:
            self._parse()

        assert self._txs is not None
        return self._txs

    def _txs_to_bytes(self, txs_details: List[TransactionInfo]):

        tx_count = len(txs_details)

        # msg_size = HDR_COMMON_OFF + tx count + (sid + hash + tx size) of each tx
        msg_size \
            = constants.HDR_COMMON_OFF + constants.UL_INT_SIZE_IN_BYTES + \
              tx_count * (
                      constants.UL_INT_SIZE_IN_BYTES + bxcommon.utils.crypto.SHA256_HASH_LEN + constants.UL_INT_SIZE_IN_BYTES)

        # msg_size += size of each tx
        for tx_info in txs_details:
            msg_size += len(tx_info.contents)

        buf = bytearray(msg_size)
        off = constants.HDR_COMMON_OFF

        struct.pack_into('<L', buf, off, len(txs_details))
        off += constants.UL_INT_SIZE_IN_BYTES

        for tx_info in txs_details:
            struct.pack_into('<L', buf, off, tx_info.short_id)
            off += constants.UL_INT_SIZE_IN_BYTES

            buf[off:off + bxcommon.utils.crypto.SHA256_HASH_LEN] = tx_info.hash
            off += bxcommon.utils.crypto.SHA256_HASH_LEN

            struct.pack_into('<L', buf, off, len(tx_info.contents))
            off += constants.UL_INT_SIZE_IN_BYTES

            buf[off:off + len(tx_info.contents)] = tx_info.contents
            off += len(tx_info.contents)

        return buf

    def _parse(self):
        txs = []

        off = constants.HDR_COMMON_OFF

        txs_count, = struct.unpack_from('<L', self.buf, off)
        off += constants.UL_INT_SIZE_IN_BYTES

        logger.debug("Block recovery: received {0} txs in the message.".format(txs_count))

        for tx_index in range(txs_count):
            tx_sid, = struct.unpack_from('<L', self.buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES

            tx_hash = Sha256Hash(self._memoryview[off:off + bxcommon.utils.crypto.SHA256_HASH_LEN])
            off += bxcommon.utils.crypto.SHA256_HASH_LEN

            tx_size, = struct.unpack_from('<L', self.buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES

            tx = self._memoryview[off:off + tx_size]
            off += tx_size

            txs.append(TransactionInfo(tx_hash, tx, tx_sid))

        self._txs = txs

    def __repr__(self):
        return "TxsMessage<num_txs: {}>".format(len(self.get_txs()))
