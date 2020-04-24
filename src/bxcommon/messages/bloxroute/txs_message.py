import struct
from typing import List, Optional

import bxcommon.utils.crypto
from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.models.transaction_info import TransactionInfo
from bxcommon.utils.object_hash import Sha256Hash
from bxutils import logging
from bxutils.logging.log_level import LogLevel

logger = logging.get_logger(__name__)


class TxsMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.TRANSACTIONS
    """
    Message with tx details. Reply to GetTxsMessage.
    """

    # pyre-fixme[9]: buf has type `bytearray`; used as `None`.
    def __init__(self, txs: Optional[List[TransactionInfo]] = None, buf: bytearray = None):

        """
        Constructor. Expects list of transaction details or message bytes.

        :param txs: tuple with 3 values (tx short id, tx hash, tx contents)
        :param buf: message bytes
        """

        if buf is None:
            # pyre-fixme[6]: Expected `List[TransactionInfo]` for 1st param but got
            #  `Optional[List[TransactionInfo]]`.
            buf = self._txs_to_bytes(txs)
            super(TxsMessage, self).__init__(self.MESSAGE_TYPE, len(buf) - self.HEADER_LENGTH, buf)
        else:
            if isinstance(buf, str):
                raise TypeError("Buffer can't be string")

            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._payload_len = None
            self._payload = None

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

        tx_count = len(txs_details)

        # msg_size = HDR_COMMON_OFF + tx count + (sid + hash + tx size) of each tx
        msg_size = (
            self.HEADER_LENGTH
            + constants.UL_INT_SIZE_IN_BYTES
            + tx_count * (
                constants.UL_INT_SIZE_IN_BYTES
                + bxcommon.utils.crypto.SHA256_HASH_LEN
                + constants.UL_INT_SIZE_IN_BYTES
            )
            + constants.CONTROL_FLAGS_LEN
        )

        # msg_size += size of each tx
        for tx_info in txs_details:
            # pyre-fixme[6]: Expected `Sized` for 1st param but got
            #  `Optional[typing.Union[bytearray, memoryview]]`.
            msg_size += len(tx_info.contents)

        buf = bytearray(msg_size)
        off = self.HEADER_LENGTH

        struct.pack_into("<L", buf, off, len(txs_details))
        off += constants.UL_INT_SIZE_IN_BYTES

        for tx_info in txs_details:
            struct.pack_into("<L", buf, off, tx_info.short_id)
            off += constants.UL_INT_SIZE_IN_BYTES

            # pyre-fixme[6]: Expected `Union[typing.Iterable[int], bytes]` for 2nd
            #  param but got `Optional[Sha256Hash]`.
            buf[off:off + bxcommon.utils.crypto.SHA256_HASH_LEN] = tx_info.hash
            off += bxcommon.utils.crypto.SHA256_HASH_LEN

            # pyre-fixme[6]: Expected `Sized` for 1st param but got
            #  `Optional[typing.Union[bytearray, memoryview]]`.
            struct.pack_into("<L", buf, off, len(tx_info.contents))
            off += constants.UL_INT_SIZE_IN_BYTES

            # pyre-fixme[6]: Expected `Sized` for 1st param but got
            #  `Optional[typing.Union[bytearray, memoryview]]`.
            # pyre-fixme[6]: Expected `Union[typing.Iterable[int], bytes]` for 2nd
            #  param but got `Optional[typing.Union[bytearray, memoryview]]`.
            buf[off:off + len(tx_info.contents)] = tx_info.contents
            # pyre-fixme[6]: Expected `Sized` for 1st param but got
            #  `Optional[typing.Union[bytearray, memoryview]]`.
            off += len(tx_info.contents)

        return buf

    def _parse(self):
        txs = []

        off = self.HEADER_LENGTH

        txs_count, = struct.unpack_from("<L", self.buf, off)
        off += constants.UL_INT_SIZE_IN_BYTES

        logger.debug("Block recovery: received {} txs in the message.", txs_count)

        for _ in range(txs_count):
            tx_sid, = struct.unpack_from("<L", self.buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES

            tx_hash = Sha256Hash(self._memoryview[off:off + bxcommon.utils.crypto.SHA256_HASH_LEN])
            off += bxcommon.utils.crypto.SHA256_HASH_LEN

            tx_size, = struct.unpack_from("<L", self.buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES

            tx = self._memoryview[off:off + tx_size]
            off += tx_size

            txs.append(TransactionInfo(tx_hash, tx, tx_sid))

        self._txs = txs

    def __repr__(self):
        return "TxsMessage<num_txs: {}>".format(len(self.get_txs()))
