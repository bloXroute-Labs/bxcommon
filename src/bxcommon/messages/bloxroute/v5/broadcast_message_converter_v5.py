import struct

from bxcommon import constants
from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.messages.bloxroute.block_holding_message import BlockHoldingMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.v5.block_holding_message_v5 import BlockHoldingMessageV5
from bxcommon.messages.bloxroute.v5.broadcast_message_v5 import BroadcastMessageV5
from bxcommon.messages.bloxroute.v5.key_message_v5 import KeyMessageV5
from bxcommon.messages.bloxroute.v5.tx_message_v5 import TxMessageV5
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter
from bxcommon.utils import crypto, uuid_pack


class _BroadcastMessageConverterV5(AbstractMessageConverter):
    _MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.BROADCAST: BroadcastMessageV5,
        BloxrouteMessageType.BLOCK_HOLDING: BlockHoldingMessageV5,
        BloxrouteMessageType.KEY: KeyMessageV5,
        BloxrouteMessageType.TRANSACTION: TxMessageV5
    }

    _MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.BROADCAST: BroadcastMessage,
        BloxrouteMessageType.BLOCK_HOLDING: BlockHoldingMessage,
        BloxrouteMessageType.KEY: KeyMessage,
        BloxrouteMessageType.TRANSACTION: TxMessage
    }

    _LEFT_BREAKPOINT = AbstractBloxrouteMessage.HEADER_LENGTH + crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN
    _RIGHT_BREAKPOINT = AbstractBloxrouteMessage.HEADER_LENGTH + crypto.SHA256_HASH_LEN + \
                        constants.NETWORK_NUM_LEN + constants.NODE_ID_SIZE_IN_BYTES

    def convert_to_older_version(self, msg: AbstractInternalMessage) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING:
            raise ValueError(f"Tried to convert unexpected new message type to v5: {msg_type}")

        old_version_msg_class = self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING[msg_type]
        old_version_payload_len = msg.payload_len() - constants.NODE_ID_SIZE_IN_BYTES

        old_version_msg_bytes = bytearray(msg.rawbytes()[:self._LEFT_BREAKPOINT])
        old_version_msg_bytes.extend(bytearray(msg.rawbytes()[self._RIGHT_BREAKPOINT:]))

        struct.pack_into("<12sL", old_version_msg_bytes, AbstractBloxrouteMessage.STARTING_BYTES_LEN, msg_type,
                         old_version_payload_len)
        return AbstractBloxrouteMessage.initialize_class(old_version_msg_class, old_version_msg_bytes,
                                                         (msg_type, old_version_payload_len))

    def convert_from_older_version(self, msg: AbstractInternalMessage) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING:
            raise ValueError(f"Tried to convert unexpected old message type to v6: {msg_type}")

        new_msg_class = self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING[msg_type]
        new_payload_len = msg.payload_len() + constants.NODE_ID_SIZE_IN_BYTES

        new_msg_bytes = bytearray(AbstractBloxrouteMessage.HEADER_LENGTH + new_payload_len)
        new_msg_bytes[:self._LEFT_BREAKPOINT] = msg.rawbytes()[:self._LEFT_BREAKPOINT]
        new_msg_bytes[self._RIGHT_BREAKPOINT:] = msg.rawbytes()[self._LEFT_BREAKPOINT:]

        # pack empty source id for old gateways, since message converters are singletons
        # and source ids for gateway don't matter anyway
        struct.pack_into("<16s", new_msg_bytes, self._LEFT_BREAKPOINT, uuid_pack.to_bytes(""))

        return AbstractBloxrouteMessage.initialize_class(new_msg_class, new_msg_bytes, (msg_type, new_payload_len))

    def convert_first_bytes_to_older_version(self, first_msg_bytes: memoryview) -> memoryview:
        if len(first_msg_bytes) < AbstractBloxrouteMessage.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - \
                constants.CONTROL_FLAGS_LEN:
            raise ValueError("Not enough bytes to convert.")
        command, payload_len = BroadcastMessage.unpack(first_msg_bytes)

        result_bytes = bytearray(len(first_msg_bytes) - constants.NODE_ID_SIZE_IN_BYTES)

        result_bytes[:AbstractBroadcastMessage.SOURCE_ID_OFFSET] = \
            first_msg_bytes[:AbstractBroadcastMessage.SOURCE_ID_OFFSET]
        result_bytes[AbstractBroadcastMessage.SOURCE_ID_OFFSET:] = \
            first_msg_bytes[AbstractBroadcastMessage.SOURCE_ID_OFFSET + constants.NODE_ID_SIZE_IN_BYTES:]

        struct.pack_into("<12sL", result_bytes, constants.STARTING_SEQUENCE_BYTES_LEN, command,
                         payload_len - constants.NODE_ID_SIZE_IN_BYTES)

        return memoryview(result_bytes)

    def convert_first_bytes_from_older_version(self, first_msg_bytes: memoryview) -> memoryview:
        if len(first_msg_bytes) < AbstractBloxrouteMessage.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - \
                constants.CONTROL_FLAGS_LEN:
            raise ValueError("Not enough bytes to convert.")
        command, payload_len = BroadcastMessageV5.unpack(first_msg_bytes)

        result_bytes = bytearray(len(first_msg_bytes) + constants.NODE_ID_SIZE_IN_BYTES)

        result_bytes[:AbstractBroadcastMessage.SOURCE_ID_OFFSET] = \
            first_msg_bytes[:AbstractBroadcastMessage.SOURCE_ID_OFFSET]
        result_bytes[AbstractBroadcastMessage.SOURCE_ID_OFFSET + constants.NODE_ID_SIZE_IN_BYTES:] = \
            first_msg_bytes[AbstractBroadcastMessage.SOURCE_ID_OFFSET:]

        struct.pack_into("<12sL", result_bytes, constants.STARTING_SEQUENCE_BYTES_LEN, command,
                         payload_len + constants.NODE_ID_SIZE_IN_BYTES)

        return memoryview(result_bytes)

    def convert_last_bytes_to_older_version(self, last_msg_bytes: memoryview) -> memoryview:
        return last_msg_bytes

    def convert_last_bytes_from_older_version(self, last_msg_bytes: memoryview) -> memoryview:
        return last_msg_bytes

    def get_message_size_change_to_older_version(self) -> int:
        return -constants.NODE_ID_SIZE_IN_BYTES

    def get_message_size_change_from_older_version(self) -> int:
        return constants.NODE_ID_SIZE_IN_BYTES


broadcast_message_converter_v5 = _BroadcastMessageConverterV5()
