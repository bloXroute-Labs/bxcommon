import struct
from typing import List, Optional

from bxcommon.constants import UL_INT_SIZE_IN_BYTES, CONTROL_FLAGS_LEN
from bxcommon.messages.bloxroute import blocks_short_ids_serializer
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.blocks_short_ids_serializer import BlockShortIds
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxutils.logging.log_level import LogLevel


class TxServiceSyncBlocksShortIdsMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.TX_SERVICE_SYNC_BLOCKS_SHORT_IDS

    """
    Message used to send information about block short ids from requested relay
    """

    def __init__(
            self, network_num: Optional[int] = None, blocks_short_ids: Optional[List[BlockShortIds]] = None,
            buf: Optional[bytearray] = None
    ):
        # pyre-fixme[8]: Attribute has type `bytearray`; used as `Optional[bytearray]`.
        self.buf: bytearray = buf
        # pyre-fixme[8]: Attribute has type `int`; used as `Optional[int]`.
        self._network_num: int = network_num
        # pyre-fixme[8]: Attribute has type `int`; used as `Optional[int]`.
        self._block_count: int = len(blocks_short_ids) if blocks_short_ids is not None else None
        # pyre-fixme[8]: Attribute has type `List[BlockShortIds]`; used as
        #  `Optional[List[BlockShortIds]]`.
        self._blocks_short_ids: List[BlockShortIds] = blocks_short_ids

        if blocks_short_ids is not None and buf is None:
            self.buf = bytearray(
                self.HEADER_LENGTH +
                2 * UL_INT_SIZE_IN_BYTES
            )

            self._parse()

        self.buf.extend(bytearray(CONTROL_FLAGS_LEN))
        super(TxServiceSyncBlocksShortIdsMessage, self).__init__(
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

    def block_count(self) -> int:
        if self._block_count is None:
            off = self.HEADER_LENGTH + UL_INT_SIZE_IN_BYTES
            self._block_count, = struct.unpack_from("<L", self._memoryview, off)
        return self._block_count

    def blocks_short_ids(self) -> List[BlockShortIds]:
        offset = self.HEADER_LENGTH + 2 * UL_INT_SIZE_IN_BYTES
        return blocks_short_ids_serializer.deserialize_blocks_short_ids_from_buffer(
            self._memoryview, offset, self.block_count()
        )

    def __repr__(self) -> str:
        return "{}<network_num: {}, block_count: {}".\
            format(self.__class__.__name__, self.network_num(), self.block_count())

    def _parse(self) -> None:
        off = self.HEADER_LENGTH
        struct.pack_into("<LL", self.buf, off, self._network_num, self._block_count)
        off += UL_INT_SIZE_IN_BYTES * 2

        self.buf.extend(blocks_short_ids_serializer.serialize_blocks_short_ids_into_bytes(self._blocks_short_ids))
