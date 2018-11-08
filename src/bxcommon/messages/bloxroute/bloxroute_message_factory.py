from bxcommon.messages.abstract_message_factory import AbstractMessageFactory
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.message import Message
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.utils.crypto import SHA256_HASH_LEN
from bxcommon.utils.object_hash import ObjectHash


class _BloxrouteMessageFactory(AbstractMessageFactory):
    _MESSAGE_TYPE_MAPPING = {
        BloxrouteMessageType.HELLO: HelloMessage,
        BloxrouteMessageType.ACK: AckMessage,
        BloxrouteMessageType.PING: PingMessage,
        BloxrouteMessageType.PONG: PongMessage,
        BloxrouteMessageType.BROADCAST: BroadcastMessage,
        BloxrouteMessageType.TRANSACTION: TxMessage,
        BloxrouteMessageType.GET_TRANSACTIONS: GetTxsMessage,
        BloxrouteMessageType.TRANSACTIONS: TxsMessage,
        BloxrouteMessageType.KEY: KeyMessage
    }

    def __init__(self):
        super(_BloxrouteMessageFactory, self).__init__()
        self.message_type_mapping = self._MESSAGE_TYPE_MAPPING
        self.base_message_type = Message

    def get_message_hash_preview(self, input_buffer):
        header_plus_hash_length = self.base_message_type.HEADER_LENGTH + SHA256_HASH_LEN
        is_full_message, _command, payload_length = self.get_message_header_preview(input_buffer)
        if payload_length is None or input_buffer.length < header_plus_hash_length:
            return False, None, None
        else:
            message_hash = input_buffer.peek_message(header_plus_hash_length)[self.base_message_type.HEADER_LENGTH:
                                                                              header_plus_hash_length]
            return is_full_message, ObjectHash(message_hash), payload_length


bloxroute_message_factory = _BloxrouteMessageFactory()
