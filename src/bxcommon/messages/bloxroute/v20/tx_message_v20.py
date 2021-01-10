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
from bxcommon.models.transaction_flag import TransactionFlag
from bxcommon.utils.object_hash import Sha256Hash


class TxMessageV20(AbstractBroadcastMessage):
    PAYLOAD_LENGTH = (
        AbstractBroadcastMessage.PAYLOAD_LENGTH
        + constants.SID_LEN
        + constants.TRANSACTION_FLAG_LEN
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
        transaction_flag: Optional[TransactionFlag] = None,
        timestamp: Union[int, float] = constants.NULL_TX_TIMESTAMP,
        buf: Optional[Union[bytearray, memoryview]] = None,
    ):
        self._short_id = None
        self._tx_val: Optional[memoryview] = None
        self._transaction_flag = None
        self._timestamp = None

        # override payload length for variable length message
        if tx_val is not None:
            # pylint: disable=invalid-name
            self.PAYLOAD_LENGTH = (
                AbstractBroadcastMessage.PAYLOAD_LENGTH
                + constants.SID_LEN
                + constants.TRANSACTION_FLAG_LEN
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

            if transaction_flag is None:
                transaction_flag = TransactionFlag.NO_FLAGS
            struct.pack_into("<H", self.buf, off, transaction_flag.value)
            off += constants.TRANSACTION_FLAG_LEN

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
            f"transaction_flag: {self.transaction_flag()}, "
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

    def transaction_flag(self) -> TransactionFlag:
        if self._transaction_flag is None:
            off = (
                self.HEADER_LENGTH
                + AbstractBroadcastMessage.PAYLOAD_LENGTH
                + constants.SID_LEN
                - constants.CONTROL_FLAGS_LEN
            )

            (transaction_flag, ) = struct.unpack_from("<H", self.buf, off)
            self._transaction_flag = TransactionFlag(transaction_flag)
        assert self._transaction_flag is not None
        return TransactionFlag(self._transaction_flag)

    def set_transaction_flag(self, flag: TransactionFlag) -> None:
        off = (
            self.HEADER_LENGTH
            + AbstractBroadcastMessage.PAYLOAD_LENGTH
            + constants.SID_LEN
            - constants.CONTROL_FLAGS_LEN
        )
        self._transaction_flag = flag
        struct.pack_into("<H", self.buf, off, flag.value)

    def timestamp(self) -> int:
        if self._timestamp is None:
            off = (
                self.HEADER_LENGTH
                + AbstractBroadcastMessage.PAYLOAD_LENGTH
                + constants.SID_LEN
                + constants.TRANSACTION_FLAG_LEN
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
                    + constants.TRANSACTION_FLAG_LEN
                    + constants.UL_INT_SIZE_IN_BYTES
                    - constants.CONTROL_FLAGS_LEN
                )
                self._tx_val = self._memoryview[
                    off : self.HEADER_LENGTH
                    + self.payload_len()
                    - constants.CONTROL_FLAGS_LEN
                ]

        tx_val = self._tx_val
        assert tx_val is not None
        return tx_val

    def is_compact(self) -> bool:
        return self.tx_val() == self.EMPTY_TX_VAL

    def set_timestamp(self, timestamp: Union[float, int]):
        timestamp = int(timestamp)
        self._timestamp = timestamp
        off = (
            self.HEADER_LENGTH
            + AbstractBroadcastMessage.PAYLOAD_LENGTH
            + constants.SID_LEN
            + constants.TRANSACTION_FLAG_LEN
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
            + constants.TRANSACTION_FLAG_LEN
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

    def quota_type(self) -> QuotaType:
        return self.transaction_flag().get_quota_type()
