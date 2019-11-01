import struct
from typing import Type

from bxcommon import constants
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.messages.abstract_message_factory import AbstractMessageFactory
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
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
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash


class _BloxrouteMessageFactoryV4(AbstractMessageFactory):
    _MESSAGE_TYPE_MAPPING = {
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

    def __init__(self):
        super(_BloxrouteMessageFactoryV4, self).__init__()
        self.message_type_mapping = self._MESSAGE_TYPE_MAPPING

    def get_base_message_type(self) -> Type[AbstractMessage]:
        return MessageV4

    def get_hashed_message_preview_from_input_buffer(self, input_buffer):
        """
        Peeks the hash and network number from hashed messages.
        Currently, only Broadcast messages are supported here.
        :param input_buffer
        :return: is full header, message hash, network number, payload length
        """
        hash_header_length = self.base_message_type.HEADER_LENGTH + crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN
        _is_full_message, _command, payload_length = self.get_message_header_preview_from_input_buffer(input_buffer)
        is_full_header = input_buffer.length >= hash_header_length
        if payload_length is None or not is_full_header:
            return False, None, None, None
        else:
            hash_header = input_buffer.peek_message(hash_header_length)

            offset = self.base_message_type.HEADER_LENGTH
            message_hash = hash_header[offset:offset + crypto.SHA256_HASH_LEN]
            offset += crypto.SHA256_HASH_LEN

            network_num, = struct.unpack_from("<L", hash_header[offset:offset + constants.NETWORK_NUM_LEN])
            return is_full_header, Sha256Hash(message_hash), network_num, payload_length


bloxroute_message_factory_v4 = _BloxrouteMessageFactoryV4()
