import struct
from typing import Optional, Union

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_broadcast_message import (
    AbstractBroadcastMessage,
)
from bxcommon.messages.bloxroute.bloxroute_message_type import (
    BloxrouteMessageType,
)
from bxcommon.models.quota_type_model import QuotaType
from bxcommon.utils.object_hash import Sha256Hash


class TxMessageV15(AbstractBroadcastMessage):
    PAYLOAD_LENGTH = (
        AbstractBroadcastMessage.PAYLOAD_LENGTH
        + constants.SID_LEN
        + constants.QUOTA_FLAG_LEN
        + constants.UL_INT_SIZE_IN_BYTES
    )
    MESSAGE_TYPE = BloxrouteMessageType.TRANSACTION
    EMPTY_TX_VAL = memoryview(bytes())

    def __init__(
        self,
        message_hash: Optional[Sha256Hash] = None,
        network_num: Optional[int] = None,
        source_id: str = "",
        short_id: int = constants.NULL_TX_SID,
        tx_val: Union[bytearray, bytes, memoryview, None] = None,
        quota_type: Optional[QuotaType] = None,
        timestamp: Union[int, float] = constants.NULL_TX_TIMESTAMP,
        buf: Optional[Union[bytearray, memoryview]] = None,
    ):
        self._short_id = None
        self._tx_val: Optional[memoryview] = None
        self._tx_quota_type = None
        self._timestamp = None

        # override payload length for variable length message
        if tx_val is not None:
            # pylint: disable=invalid-name
            self.PAYLOAD_LENGTH = (
                AbstractBroadcastMessage.PAYLOAD_LENGTH
                + constants.SID_LEN
                + constants.QUOTA_FLAG_LEN
                + constants.UL_INT_SIZE_IN_BYTES
                + len(tx_val)
            )
        super().__init__(message_hash, network_num, source_id, buf)

        if buf is None:
            # minus control flag
            off = (
                self.HEADER_LENGTH
                + AbstractBroadcastMessage.PAYLOAD_LENGTH
                - constants.CONTROL_FLAGS_LEN
            )

            struct.pack_into("<L", self.buf, off, short_id)
            off += constants.SID_LEN

            if quota_type is None:
                quota_type = QuotaType.FREE_DAILY_QUOTA
            struct.pack_into("<B", self.buf, off, quota_type.value)
            off += constants.QUOTA_FLAG_LEN

            struct.pack_into("<L", self.buf, off, int(timestamp))
            off += constants.UL_INT_SIZE_IN_BYTES

            if tx_val is not None:
                self.buf[off:off + len(tx_val)] = tx_val

    def __repr__(self):
        return (
            f"TxMessage<"
            f"tx_hash: {self.tx_hash()}, "
            f"short_id: {self.short_id()}, "
            f"network_num: {self.network_num()}, "
            f"compact: {self.is_compact()}, "
            f"source_id: {self.source_id_as_str()}, "
            f"quota_type: {self.quota_type()}, "
            f"timestamp: {self.timestamp()}"
            f">"
        )

    def tx_hash(self) -> Sha256Hash:
        return self.message_hash()

    def short_id(self) -> int:
        if self._short_id is None:
            off = (
                self.HEADER_LENGTH
                + AbstractBroadcastMessage.PAYLOAD_LENGTH
                - constants.CONTROL_FLAGS_LEN
            )
            (self._short_id,) = struct.unpack_from("<L", self.buf, off)
        # pyre-fixme[7]: Expected `int` but got `None`.
        return self._short_id

    def has_short_id(self) -> bool:
        return self.short_id() != constants.NULL_TX_SID

    def quota_type(self) -> QuotaType:
        if self._tx_quota_type is None:
            off = (
                self.HEADER_LENGTH
                + AbstractBroadcastMessage.PAYLOAD_LENGTH
                + constants.SID_LEN
                - constants.CONTROL_FLAGS_LEN
            )

            (tx_quota_type_flag,) = struct.unpack_from("<B", self.buf, off)
            self._tx_quota_type = QuotaType(tx_quota_type_flag)
        assert self._tx_quota_type is not None
        # pyre-fixme[7]: Expected `QuotaType` but got `None`.
        return self._tx_quota_type

    def timestamp(self) -> int:
        if self._timestamp is None:
            off = (
                self.HEADER_LENGTH
                + AbstractBroadcastMessage.PAYLOAD_LENGTH
                + constants.SID_LEN
                + constants.QUOTA_FLAG_LEN
                - constants.CONTROL_FLAGS_LEN
            )
            (self._timestamp,) = struct.unpack_from("<L", self.buf, off)
        # pyre-fixme[7]: Expected `int` but got `None`.
        return self._timestamp

    def tx_val(self) -> memoryview:
        if self._tx_val is None:
            if self.payload_len() == 0:
                self._tx_val = self.EMPTY_TX_VAL
            else:
                off = (
                    self.HEADER_LENGTH
                    + AbstractBroadcastMessage.PAYLOAD_LENGTH
                    + constants.SID_LEN
                    + constants.QUOTA_FLAG_LEN
                    + constants.UL_INT_SIZE_IN_BYTES
                    - constants.CONTROL_FLAGS_LEN
                )
                self._tx_val = self._memoryview[
                    off : self.HEADER_LENGTH
                    + self.payload_len()
                    - constants.CONTROL_FLAGS_LEN
                ]

        assert self._tx_val is not None
        # pyre-fixme[7]: Expected `memoryview` but got `Optional[memoryview]`.
        return self._tx_val

    def is_compact(self) -> bool:
        return self.tx_val() == self.EMPTY_TX_VAL

    def set_timestamp(self, timestamp: Union[float, int]):
        timestamp = int(timestamp)
        self._timestamp = timestamp
        off = (
            self.HEADER_LENGTH
            + AbstractBroadcastMessage.PAYLOAD_LENGTH
            + constants.SID_LEN
            + constants.QUOTA_FLAG_LEN
            - constants.CONTROL_FLAGS_LEN
        )
        struct.pack_into("<L", self.buf, off, timestamp)

    def clear_short_id(self):
        off = (
            self.HEADER_LENGTH
            + AbstractBroadcastMessage.PAYLOAD_LENGTH
            - constants.CONTROL_FLAGS_LEN
        )
        struct.pack_into("<L", self.buf, off, constants.NULL_TX_SID)
        self._short_id = constants.NULL_TX_SID

    def clear_timestamp(self):
        off = (
            self.HEADER_LENGTH
            + AbstractBroadcastMessage.PAYLOAD_LENGTH
            + constants.SID_LEN
            + constants.QUOTA_FLAG_LEN
            - constants.CONTROL_FLAGS_LEN
        )
        struct.pack_into("<L", self.buf, off, constants.NULL_TX_TIMESTAMP)
        self._timestamp = constants.NULL_TX_TIMESTAMP

    def clear_protected_fields(self):
        """
        Clears attributes that should be set if coming from a gateway
        connection.
        """
        self.clear_short_id()
        self.clear_timestamp()
