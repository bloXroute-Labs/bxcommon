import struct
from typing import Optional, List, Union

from bxcommon.constants import UL_INT_SIZE_IN_BYTES, CONTROL_FLAGS_LEN, UL_SHORT_SIZE_IN_BYTES
from bxcommon.messages.bloxroute import txs_serializer
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.txs_serializer import TxContentShortIds
from bxutils.logging.log_level import LogLevel


class TxServiceSyncTxsMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.TX_SERVICE_SYNC_TXS
    """
    Message used to send information about txs hash from requested relay
    """

    def __init__(
            self, network_num: Optional[int] = None,
            txs_content_short_ids: Optional[List[TxContentShortIds]] = None,
            txs_buffer: Optional[Union[memoryview, bytearray]] = None,
            tx_count: Optional[int] = None,
            buf: Optional[bytearray] = None
    ):
        # pyre-fixme[8]: Attribute has type `int`; used as `Optional[int]`.
        self._network_num: int = network_num
        # pyre-fixme[8]: Attribute has type `int`; used as `Optional[int]`.
        self._tx_count: int = len(txs_content_short_ids) if txs_content_short_ids is not None else None
        # pyre-fixme[8]: Attribute has type `List[TxContentShortIds]`; used as
        #  `Optional[List[TxContentShortIds]]`.
        self._txs_content_short_ids: List[TxContentShortIds] = txs_content_short_ids

        if txs_content_short_ids is not None and buf is None:
            self.buf = bytearray(self.HEADER_LENGTH + UL_INT_SIZE_IN_BYTES + UL_INT_SIZE_IN_BYTES)
            self._txs_content_short_ids_serialize()
            self.buf.extend(bytearray(CONTROL_FLAGS_LEN))
        elif txs_buffer is not None and buf is None:
            txs_offset = self.HEADER_LENGTH + UL_INT_SIZE_IN_BYTES +  UL_INT_SIZE_IN_BYTES
            self.buf = bytearray(txs_offset + len(txs_buffer) + CONTROL_FLAGS_LEN)
            # pyre-fixme[8]: Attribute has type `int`; used as `Optional[int]`.
            self._tx_count = tx_count
            struct.pack_into("<LL", self.buf, self.HEADER_LENGTH, self._network_num, self._tx_count)
            self.buf[txs_offset:txs_offset + len(txs_buffer)] = txs_buffer
        elif buf is not None:
            self.buf = buf

        super(TxServiceSyncTxsMessage, self).__init__(
            self.MESSAGE_TYPE,
            len(self.buf) - self.HEADER_LENGTH,
            self.buf
        )

    def log_level(self) -> LogLevel:
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

    def txs_content_short_ids(self) -> List[TxContentShortIds]:
        offset = self.HEADER_LENGTH + UL_INT_SIZE_IN_BYTES + UL_INT_SIZE_IN_BYTES
        return txs_serializer.deserialize_txs_content_short_ids_from_buffer(self._memoryview, offset, self.tx_count())

    def __repr__(self) -> str:
        return "{}<network_num: {}, tx_count: {}>".format(self.__class__.__name__, self.network_num(), self.tx_count())

    def _txs_content_short_ids_serialize(self) -> None:
        off = self.HEADER_LENGTH
        tx_count = len(self._txs_content_short_ids)
        struct.pack_into("<LL", self.buf, off, self._network_num, tx_count)
        off += UL_INT_SIZE_IN_BYTES + UL_SHORT_SIZE_IN_BYTES
        self.buf.extend(
            txs_serializer.serialize_txs_content_short_ids_into_bytes(
                self._txs_content_short_ids, self.network_num()
            )
        )
