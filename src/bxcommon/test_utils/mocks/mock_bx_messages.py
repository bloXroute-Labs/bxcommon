import struct

from bxcommon import constants
from bxcommon.constants import DEFAULT_NETWORK_NUM
from bxcommon.messages.bloxroute import compact_block_short_ids_serializer
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.models.broadcast_message_type import BroadcastMessageType
from bxcommon.test_utils import helpers
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash


def hello_message():
    return HelloMessage(protocol_version=bloxroute_version_manager.CURRENT_PROTOCOL_VERSION,
                        network_num=DEFAULT_NETWORK_NUM)


def broadcast_key_pair(short_ids=None, network_num=0):
    if short_ids is None:
        short_ids = [1, 10, 99, 187]
    broadcast_message_hash = Sha256Hash(helpers.generate_bytearray(crypto.SHA256_HASH_LEN))
    broadcast_message_bytes = bytearray(constants.UL_ULL_SIZE_IN_BYTES)
    broadcast_message_bytes.extend(helpers.generate_bytearray(500))
    struct.pack_into("<Q", broadcast_message_bytes, 0, len(broadcast_message_bytes))
    broadcast_message_bytes.extend(compact_block_short_ids_serializer.serialize_short_ids_into_bytes(short_ids))
    key_bytes, enc_broadcast_message_bytes = crypto.symmetric_encrypt(bytes(broadcast_message_bytes))

    broadcast_message = BroadcastMessage(broadcast_message_hash, network_num, "", BroadcastMessageType.BLOCK, True,
                                         enc_broadcast_message_bytes)
    key_message = KeyMessage(broadcast_message_hash, network_num, "", key_bytes)
    return broadcast_message, key_message


def tx_message(
    network_num: int = 1,
    source_id: str = "",
    short_id: int = constants.NULL_TX_SID
) -> TxMessage:
    return TxMessage(
        helpers.generate_object_hash(),
        network_num,
        source_id,
        short_id,
        helpers.generate_bytearray(250),
        account_id=helpers.generate_object_hash().to_string()
    )
