import struct
from typing import Optional

import bxcommon.utils.crypto
from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.models.transaction_info import TransactionInfo
from bxcommon.utils.object_hash import Sha256Hash
from bxutils import logging
from bxutils.logging.log_level import LogLevel

logger = logging.get_logger(__name__)


class TxContentsMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.TX_CONTENTS

    """
    Message with tx details. Reply to GetTxContentsMessage.
    """

    def __init__(self, network_num: Optional[int] = None, tx_info: Optional[TransactionInfo] = None,
                 buf: Optional[bytearray] = None):
        """
        Constructor. Expects network number and transaction details, or message bytes.

        :param network_num: blockchain network number
        :param tx: tuple with 3 values (tx short id, tx hash, tx contents)
        :param buf: message bytes
        """
        # msg_size = HDR_COMMON_OFF + network_num + sid + hash + tx size
        msg_size = self.HEADER_LENGTH + constants.NETWORK_NUM_LEN + \
                   constants.SID_LEN + bxcommon.utils.crypto.SHA256_HASH_LEN + constants.UL_INT_SIZE_IN_BYTES + \
                   constants.CONTROL_FLAGS_LEN

        self._network_num = None
        self._tx_info = None

        if buf is None:
            # pyre-fixme[16]: `Optional` has no attribute `contents`.
            tx_contents_len = len(tx_info.contents)
            msg_size += tx_contents_len
            buf = bytearray(msg_size)
            off = self.HEADER_LENGTH

            struct.pack_into("<L", buf, off, network_num)
            off += constants.NETWORK_NUM_LEN

            # pyre-fixme[16]: `Optional` has no attribute `short_id`.
            struct.pack_into("<L", buf, off, tx_info.short_id)
            off += constants.SID_LEN

            # pyre-fixme[16]: `Optional` has no attribute `hash`.
            buf[off:off + bxcommon.utils.crypto.SHA256_HASH_LEN] = tx_info.hash
            off += bxcommon.utils.crypto.SHA256_HASH_LEN

            struct.pack_into("<L", buf, off, tx_contents_len)
            off += constants.UL_INT_SIZE_IN_BYTES

            buf[off:off + tx_contents_len] = tx_info.contents
            off += tx_contents_len

            super(TxContentsMessage, self).__init__(self.MESSAGE_TYPE, msg_size - self.HEADER_LENGTH, buf)
        else:
            if isinstance(buf, str):
                raise TypeError("Buffer can't be string")

            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._payload_len = None
            self._payload = None

    def log_level(self) -> LogLevel:
        return LogLevel.DEBUG

    def network_num(self) -> int:
        if self._network_num is None:
            self._parse()

        assert self._network_num is not None
        # pyre-fixme[7]: Expected `int` but got `None`.
        return self._network_num

    def get_tx_info(self) -> TransactionInfo:
        if self._tx_info is None:
            self._parse()

        assert self._tx_info is not None
        # pyre-fixme[7]: Expected `TransactionInfo` but got `None`.
        return self._tx_info

    def _parse(self) -> None:
        off = self.HEADER_LENGTH

        self._network_num, = struct.unpack_from("<L", self.buf, off)
        off += constants.NETWORK_NUM_LEN

        tx_sid, = struct.unpack_from("<L", self.buf, off)
        off += constants.SID_LEN

        tx_hash = Sha256Hash(self._memoryview[off:off + bxcommon.utils.crypto.SHA256_HASH_LEN])
        off += bxcommon.utils.crypto.SHA256_HASH_LEN

        tx_size, = struct.unpack_from("<L", self.buf, off)
        off += constants.UL_INT_SIZE_IN_BYTES

        tx = self._memoryview[off:off + tx_size]
        off += tx_size

        self._tx_info = TransactionInfo(tx_hash, tx, tx_sid)

    def __repr__(self) -> str:
        return f"TxContentsMessage<network_num: {self.network_num()}, tx_hash: {self.get_tx_info().hash}, " \
               f"sid: {self.get_tx_info().short_id}>"
