import struct
from typing import Optional, Union

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.utils.object_hash import Sha256Hash


class TxMessageV6(AbstractBroadcastMessage):
    PAYLOAD_LENGTH = AbstractBroadcastMessage.PAYLOAD_LENGTH + constants.SID_LEN
    MESSAGE_TYPE = BloxrouteMessageType.TRANSACTION
    EMPTY_TX_VAL = memoryview(bytes())

    def __init__(self, message_hash: Optional[Sha256Hash] = None, network_num: Optional[int] = None,
                 source_id: str = "", short_id: int = constants.NULL_TX_SID,
                 tx_val: Union[bytearray, bytes, memoryview, None] = None,
                 buf: Optional[bytearray] = None):
        self._short_id = None
        self._tx_val: Optional[memoryview] = None

        # override payload length for variable length message
        if tx_val is not None:
            # pylint: disable=invalid-name
            self.PAYLOAD_LENGTH = AbstractBroadcastMessage.PAYLOAD_LENGTH + constants.SID_LEN + len(tx_val)
        super().__init__(message_hash, network_num, source_id, buf)

        if buf is None:
            # minus control flag
            off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - constants.CONTROL_FLAGS_LEN

            struct.pack_into("<L", self.buf, off, short_id)
            off += constants.SID_LEN

            if tx_val is not None:
                self.buf[off:off + len(tx_val)] = tx_val

    def tx_hash(self) -> Sha256Hash:
        return self.message_hash()

    def short_id(self) -> int:
        if self._short_id is None:
            off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - constants.CONTROL_FLAGS_LEN
            self._short_id, = struct.unpack_from("<L", self.buf, off)
        # pyre-fixme[7]: Expected `int` but got `None`.
        return self._short_id

    def tx_val(self) -> memoryview:
        if self._tx_val is None:
            if self.payload_len() == 0:
                self._tx_val = self.EMPTY_TX_VAL
            else:
                off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH + constants.SID_LEN - \
                      constants.CONTROL_FLAGS_LEN
                self._tx_val = self._memoryview[
                               off:self.HEADER_LENGTH + self.payload_len() - constants.CONTROL_FLAGS_LEN]

        assert self._tx_val is not None
        # pyre-fixme[7]: Expected `memoryview` but got `Optional[memoryview]`.
        return self._tx_val

    def __repr__(self) -> str:
        return ("TxMessage<tx_hash: {}, short_id: {}, network_num: {}, compact: {}, source_id: {}>"
                .format(self.tx_hash(), self.short_id(), self.network_num(), self.tx_val() == self.EMPTY_TX_VAL,
                        self.source_id_as_str()))
