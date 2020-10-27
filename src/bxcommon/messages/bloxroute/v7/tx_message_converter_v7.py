import struct

from bxcommon import constants
from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.abstract_bloxroute_message import (
    AbstractBloxrouteMessage,
)
from bxcommon.messages.bloxroute.abstract_broadcast_message import (
    AbstractBroadcastMessage,
)
from bxcommon.messages.bloxroute.bloxroute_message_type import (
    BloxrouteMessageType,
)
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.v7.tx_message_v7 import TxMessageV7
from bxcommon.messages.versioning.abstract_message_converter import (
    AbstractMessageConverter,
)


class _TxMessageConverterV7(AbstractMessageConverter):
    _MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.TRANSACTION: TxMessageV7
    }

    _MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.TRANSACTION: TxMessage
    }

    _BASE_LENGTH = (
        AbstractBroadcastMessage.HEADER_LENGTH
        + AbstractBroadcastMessage.PAYLOAD_LENGTH
        - constants.CONTROL_FLAGS_LEN
    )
    _LEFT_BREAKPOINT = (
        _BASE_LENGTH + constants.SID_LEN + constants.QUOTA_FLAG_LEN
    )
    _RIGHT_BREAKPOINT = (
        _BASE_LENGTH
        + constants.SID_LEN
        + constants.TRANSACTION_FLAG_LEN
        + constants.UL_INT_SIZE_IN_BYTES
    )

    def convert_to_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING:
            raise ValueError(
                f"Tried to convert unexpected new "
                f"message type to v7: {msg_type}"
            )

        old_version_msg_class = self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING[
            msg_type
        ]
        old_version_payload_len = (
            msg.payload_len()
            - constants.QUOTA_FLAG_LEN
            - constants.UL_INT_SIZE_IN_BYTES
        )

        old_version_msg_bytes = bytearray(
            self._LEFT_BREAKPOINT
            + len(msg.rawbytes()[self._RIGHT_BREAKPOINT :])
        )
        old_version_msg_bytes[: self._LEFT_BREAKPOINT] = msg.rawbytes()[
            : self._LEFT_BREAKPOINT
        ]
        old_version_msg_bytes[self._LEFT_BREAKPOINT :] = msg.rawbytes()[
            self._RIGHT_BREAKPOINT :
        ]

        return AbstractBloxrouteMessage.initialize_class(
            old_version_msg_class,
            old_version_msg_bytes,
            (msg_type, old_version_payload_len),
        )

    def convert_from_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING:
            raise ValueError(
                f"Tried to convert unexpected old message type to "
                f"v7: {msg_type}"
            )

        new_msg_class = self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING[msg_type]
        new_payload_len = (
            msg.payload_len() +
            constants.QUOTA_FLAG_LEN +
            constants.UL_INT_SIZE_IN_BYTES
        )

        new_msg_bytes = bytearray(
            AbstractBloxrouteMessage.HEADER_LENGTH + new_payload_len
        )
        new_msg_bytes[: self._LEFT_BREAKPOINT] = msg.rawbytes()[
            : self._LEFT_BREAKPOINT
        ]

        struct.pack_into("<B", new_msg_bytes, self._LEFT_BREAKPOINT, 0)
        struct.pack_into("<L", new_msg_bytes, self._LEFT_BREAKPOINT, 0)
        new_msg_bytes[self._RIGHT_BREAKPOINT :] = msg.rawbytes()[
            self._LEFT_BREAKPOINT :
        ]

        return AbstractBloxrouteMessage.initialize_class(
            new_msg_class, new_msg_bytes, (msg_type, new_payload_len)
        )

    def convert_first_bytes_to_older_version(
        self, first_msg_bytes: memoryview
    ) -> memoryview:
        raise NotImplementedError

    def convert_first_bytes_from_older_version(
        self, first_msg_bytes: memoryview
    ) -> memoryview:
        raise NotImplementedError

    def convert_last_bytes_to_older_version(
        self, last_msg_bytes: memoryview
    ) -> memoryview:
        raise NotImplementedError

    def convert_last_bytes_from_older_version(
        self, last_msg_bytes: memoryview
    ) -> memoryview:
        raise NotImplementedError

    def get_message_size_change_to_older_version(self) -> int:
        raise NotImplementedError

    def get_message_size_change_from_older_version(self) -> int:
        raise NotImplementedError


tx_message_converter_v7 = _TxMessageConverterV7()
