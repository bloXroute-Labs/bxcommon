from typing import Union, Tuple

from bxcommon.utils import crypto
from bxcommon.utils.blockchain_utils.btc.btc_common_utils import btc_varint_to_int
from bxcommon.utils.blockchain_utils.ont import ont_common_constants
from bxcommon.utils.blockchain_utils.ont.ont_object_hash import OntObjectHash


def ont_varint_to_int(buf: Union[memoryview, bytearray], off: int) -> Tuple[int, int]:
    return btc_varint_to_int(buf, off)


def get_txid(buffer: Union[memoryview, bytearray]) -> Tuple[OntObjectHash, int]:
    if not isinstance(buffer, memoryview):
        buffer = memoryview(buffer)
    off = 1
    txtype = buffer[off:off + 1]
    off += 1 + 40
    # Deploy type
    if txtype == ont_common_constants.ONT_TX_DEPLOY_TYPE_INDICATOR_AS_BYTEARRAY:
        buffer_length, size = ont_varint_to_int(buffer, off)
        off += buffer_length + size
        off += 1
        buffer_length, size = ont_varint_to_int(buffer, off)
        off += buffer_length + size
        buffer_length, size = ont_varint_to_int(buffer, off)
        off += buffer_length + size
        buffer_length, size = ont_varint_to_int(buffer, off)
        off += buffer_length + size
        buffer_length, size = ont_varint_to_int(buffer, off)
        off += buffer_length + size
        buffer_length, size = ont_varint_to_int(buffer, off)
        off += buffer_length + size
    # Invoke type
    elif txtype == ont_common_constants.ONT_TX_INVOKE_TYPE_INDICATOR_AS_BYTEARRAY:
        buffer_length, size = ont_varint_to_int(buffer, off)
        off += buffer_length + size

    _, size = ont_varint_to_int(buffer, off)
    off += size

    return OntObjectHash(buf=crypto.double_sha256(buffer[:off]), length=ont_common_constants.ONT_HASH_LEN), off
