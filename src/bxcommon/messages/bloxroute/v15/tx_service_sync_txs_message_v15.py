import struct
from typing import Optional, List

from bxcommon.constants import UL_INT_SIZE_IN_BYTES, CONTROL_FLAGS_LEN, UL_SHORT_SIZE_IN_BYTES
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v15 import txs_serializer_v15
from bxcommon.messages.bloxroute.v15.txs_serializer_v15 import TxContentShortIdsV15
from bxutils.logging.log_level import LogLevel


class TxServiceSyncTxsMessageV15(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.TX_SERVICE_SYNC_TXS
    """
    Message used to send information about txs hash from requested relay
    """

    def __init__(
            self, network_num: Optional[int] = None,
            txs_content_short_ids: Optional[List[TxContentShortIdsV15]] = None,
            buf: Optional[bytearray] = None
    ):
        # pyre-fixme[8]: Attribute has type `int`; used as `Optional[int]`.
        self._network_num: int = network_num
        # pyre-fixme[8]: Attribute has type `int`; used as `Optional[int]`.
        self._tx_count: int = len(txs_content_short_ids) if txs_content_short_ids is not None else None
        # pyre-fixme[8]: Attribute has type `List[TxContentShortIdsV15]`; used as
        #  `Optional[List[TxContentShortIdsV13]]`.
        self._txs_content_short_ids: List[TxContentShortIdsV15] = txs_content_short_ids

        if txs_content_short_ids is not None and buf is None:
            self.buf = bytearray(self.HEADER_LENGTH + UL_INT_SIZE_IN_BYTES + UL_INT_SIZE_IN_BYTES)
            self._parse()
        elif buf is not None:
            self.buf = buf

        self.buf.extend(bytearray(CONTROL_FLAGS_LEN))
        super(TxServiceSyncTxsMessageV15, self).__init__(
            self.MESSAGE_TYPE,
            len(self.buf) - self.HEADER_LENGTH,
            self.buf
        )

    def log_level(self):
        return LogLevel.DEBUG

    def network_num(self) -> int:
        if self._network_num is None:
            off = self.HEADER_LENGTH
            self._network_num, = struct.unpack_from("<L", self._memoryview, off)
        return self._network_num

    def tx_count(self) -> int:
        if self._tx_count is None:
            off = self.HEADER_LENGTH + UL_INT_SIZE_IN_BYTES
            self._tx_count, = struct.unpack_from("<L", self._memoryview, off)
        return self._tx_count

    def txs_content_short_ids(self) -> List[TxContentShortIdsV15]:
        offset = self.HEADER_LENGTH + UL_INT_SIZE_IN_BYTES + UL_INT_SIZE_IN_BYTES
        return txs_serializer_v15.deserialize_txs_content_short_ids_from_buffer(
            self._memoryview, offset, self.tx_count()
        )

    def __repr__(self) -> str:
        return "{}<network_num: {}, tx_count: {}".format(self.__class__.__name__, self.network_num(), self.tx_count())

    def _parse(self) -> None:
        off = self.HEADER_LENGTH
        tx_count = len(self._txs_content_short_ids)
        struct.pack_into("<LL", self.buf, off, self._network_num, tx_count)
        off += UL_INT_SIZE_IN_BYTES + UL_SHORT_SIZE_IN_BYTES

        self.buf.extend(
            txs_serializer_v15.serialize_txs_content_short_ids_into_bytes(
                self._txs_content_short_ids, self.network_num()
            )
        )
