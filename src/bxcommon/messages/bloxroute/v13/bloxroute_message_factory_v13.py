import struct
from typing import Optional, Type, NamedTuple

from bxcommon import constants
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.messages.abstract_message_factory import AbstractMessageFactory
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v13.pong_message_v13 import PongMessageV13
from bxcommon.messages.bloxroute.v14.bloxroute_message_factory_v14 import bloxroute_message_factory_v14
from bxcommon.models.broadcast_message_type import BroadcastMessageType
from bxcommon.utils import crypto, uuid_pack
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.object_hash import ConcatHash, Sha256Hash


class BroadcastMessagePreview(NamedTuple):
    is_full_header: bool
    block_hash: Optional[Sha256Hash]
    broadcast_type: Optional[BroadcastMessageType]
    message_id: Optional[ConcatHash]
    network_num: Optional[int]
    source_id: Optional[str]
    payload_length: Optional[int]


class _BloxrouteMessageFactoryV13(AbstractMessageFactory):
    _MESSAGE_TYPE_MAPPING = {
        # pylint: disable=protected-access
        **bloxroute_message_factory_v14._MESSAGE_TYPE_MAPPING,
        BloxrouteMessageType.PONG: PongMessageV13,
    }

    def __init__(self) -> None:
        super(_BloxrouteMessageFactoryV13, self).__init__(self._MESSAGE_TYPE_MAPPING)

    def get_base_message_type(self) -> Type[AbstractMessage]:
        return AbstractBloxrouteMessage

    def get_broadcast_message_preview(self, input_buffer: InputBuffer) -> BroadcastMessagePreview:
        """
        Peeks the hash and network number from hashed messages.
        Currently, only Broadcast messages are supported here.
        :param input_buffer
        :return: is full header, message hash, network number, source id, payload length
        """
        # -1 for control flag length
        broadcast_header_length = self.base_message_type.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - \
                                  constants.CONTROL_FLAGS_LEN
        is_full_header = input_buffer.length >= broadcast_header_length
        if not is_full_header:
            return BroadcastMessagePreview(False, None, None, None, None, None, None)
        else:
            _is_full_message, _command, payload_length = self.get_message_header_preview_from_input_buffer(input_buffer)

            broadcast_header = input_buffer.peek_message(broadcast_header_length)

            offset = self.base_message_type.HEADER_LENGTH

            block_hash = broadcast_header[offset:offset + crypto.SHA256_HASH_LEN]
            block_hash_with_network_num = broadcast_header[offset:
                                                           offset + crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN]
            offset += crypto.SHA256_HASH_LEN

            network_num, = struct.unpack_from("<L", broadcast_header[offset:offset + constants.NETWORK_NUM_LEN])
            offset += constants.NETWORK_NUM_LEN

            source_id = uuid_pack.from_bytes(
                struct.unpack_from("<16s", broadcast_header[offset:offset + constants.NODE_ID_SIZE_IN_BYTES])[0])
            offset += constants.NODE_ID_SIZE_IN_BYTES

            broadcast_type_bytearray = broadcast_header[offset:offset + constants.BROADCAST_TYPE_LEN]
            broadcast_type_in_str = struct.unpack_from(
                "<4s", broadcast_type_bytearray
            )[0].decode(constants.DEFAULT_TEXT_ENCODING)
            broadcast_type = BroadcastMessageType(broadcast_type_in_str)
            message_id = ConcatHash(bytearray(block_hash_with_network_num) + broadcast_type_bytearray, 0)

            return BroadcastMessagePreview(is_full_header, Sha256Hash(block_hash), broadcast_type, message_id,
                                           network_num, source_id, payload_length)

    def __repr__(self):
        return f"{self.__class__.__name__}; message_type_mapping: {self.message_type_mapping}"


bloxroute_message_factory_v13 = _BloxrouteMessageFactoryV13()
