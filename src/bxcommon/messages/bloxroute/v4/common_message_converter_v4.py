import struct

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.block_holding_message import BlockHoldingMessage
from bxcommon.messages.bloxroute.bloxroute_message_control_flags import BloxrouteMessageControlFlags
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.v4.ack_message_v4 import AckMessageV4
from bxcommon.messages.bloxroute.v4.block_holding_message_v4 import BlockHoldingMessageV4
from bxcommon.messages.bloxroute.v4.broadcast_message_v4 import BroadcastMessageV4
from bxcommon.messages.bloxroute.v4.get_txs_message_v4 import GetTxsMessageV4
from bxcommon.messages.bloxroute.v4.hello_message_v4 import HelloMessageV4
from bxcommon.messages.bloxroute.v4.key_message_v4 import KeyMessageV4
from bxcommon.messages.bloxroute.v4.message_v4 import MessageV4
from bxcommon.messages.bloxroute.v4.ping_message_v4 import PingMessageV4
from bxcommon.messages.bloxroute.v4.pong_message_v4 import PongMessageV4
from bxcommon.messages.bloxroute.v4.tx_message_v4 import TxMessageV4
from bxcommon.messages.bloxroute.v4.txs_message_v4 import TxsMessageV4
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter


class _CommonMessageConverterV4(AbstractMessageConverter):
    _MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.HELLO: HelloMessageV4,
        BloxrouteMessageType.ACK: AckMessageV4,
        BloxrouteMessageType.PING: PingMessageV4,
        BloxrouteMessageType.PONG: PongMessageV4,
        BloxrouteMessageType.BROADCAST: BroadcastMessageV4,
        BloxrouteMessageType.TRANSACTION: TxMessageV4,
        BloxrouteMessageType.GET_TRANSACTIONS: GetTxsMessageV4,
        BloxrouteMessageType.TRANSACTIONS: TxsMessageV4,
        BloxrouteMessageType.KEY: KeyMessageV4,
        BloxrouteMessageType.BLOCK_HOLDING: BlockHoldingMessageV4
    }

    _MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.HELLO: HelloMessage,
        BloxrouteMessageType.ACK: AckMessage,
        BloxrouteMessageType.PING: PingMessage,
        BloxrouteMessageType.PONG: PongMessage,
        BloxrouteMessageType.BROADCAST: BroadcastMessage,
        BloxrouteMessageType.TRANSACTION: TxMessage,
        BloxrouteMessageType.GET_TRANSACTIONS: GetTxsMessage,
        BloxrouteMessageType.TRANSACTIONS: TxsMessage,
        BloxrouteMessageType.KEY: KeyMessage,
        BloxrouteMessageType.BLOCK_HOLDING: BlockHoldingMessage
    }

    def convert_to_older_version(self, msg):
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING:
            return None

        old_version_msg_class = self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING[msg_type]
        old_version_payload_len = msg.payload_len() - constants.CONTROL_FLAGS_LEN
        old_version_msg_bytes = msg.rawbytes()[constants.STARTING_SEQUENCE_BYTES_LEN:-constants.CONTROL_FLAGS_LEN]
        struct.pack_into("<12sL", old_version_msg_bytes, 0, msg_type, old_version_payload_len)

        return MessageV4.initialize_class(old_version_msg_class, old_version_msg_bytes,
                                          (msg_type, old_version_payload_len))

    def convert_from_older_version(self, msg):
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING:
            return None

        new_msg_class = self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING[msg_type]
        new_payload_len = msg.payload_len() + constants.CONTROL_FLAGS_LEN
        new_msg_bytes = bytearray(AbstractBloxrouteMessage.HEADER_LENGTH + new_payload_len)
        new_msg_bytes[:constants.STARTING_SEQUENCE_BYTES_LEN] = constants.STARTING_SEQUENCE_BYTES
        struct.pack_into("<12sL", new_msg_bytes, constants.STARTING_SEQUENCE_BYTES_LEN, msg_type, new_payload_len)
        new_msg_bytes[constants.STARTING_SEQUENCE_BYTES_LEN:-constants.CONTROL_FLAGS_LEN] = msg.rawbytes()
        new_msg_bytes[-1] = BloxrouteMessageControlFlags.VALID

        return AbstractBloxrouteMessage.initialize_class(new_msg_class, new_msg_bytes, (msg_type, new_payload_len))

    def convert_first_bytes_to_older_version(self, first_msg_bytes):
        raise NotImplementedError()

    def convert_first_bytes_from_older_version(self, first_msg_bytes):
        raise NotImplementedError()

    def get_message_size_change_to_older_version(self):
        raise NotImplementedError()

    def get_message_size_change_from_older_version(self):
        raise NotImplementedError()


common_message_converter_v4 = _CommonMessageConverterV4()
