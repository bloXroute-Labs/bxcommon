import struct
from typing import List, Union, NamedTuple

from bxcommon.constants import UL_INT_SIZE_IN_BYTES
from bxcommon.utils.crypto import SHA256_HASH_LEN
from bxcommon.utils.object_hash import Sha256Hash


class BlockShortIds(NamedTuple):
    block_hash: Sha256Hash
    short_ids: List[int]


def get_serialized_blocks_short_ids_bytes_len(blocks_short_ids: List[BlockShortIds]) -> int:
    """
    Calculates length of list of blocks short ids serialized into bytes

    :param blocks_short_ids: list of block short ids
    :return: length of serialized bytes
    """

    return len(blocks_short_ids) * SHA256_HASH_LEN + \
           len(blocks_short_ids) * UL_INT_SIZE_IN_BYTES + \
           sum([len(block_short_ids.short_ids) for block_short_ids in blocks_short_ids]) * UL_INT_SIZE_IN_BYTES


def serialize_blocks_short_ids_into_bytes(block_short_ids: List[BlockShortIds]) -> bytearray:
    """
    Serializes list of block short ids into bytes

    :param block_short_ids: list of tuple block short ids
    :return: bytearray with serialized bytes
    """

    buffer = bytearray(get_serialized_blocks_short_ids_bytes_len(block_short_ids))
    off = 0
    for block_short_id in block_short_ids:
        buffer[off:off + SHA256_HASH_LEN] = block_short_id.block_hash.binary
        off += SHA256_HASH_LEN
        struct.pack_into("<L", buffer, off, len(block_short_id.short_ids))
        off += UL_INT_SIZE_IN_BYTES
        for short_id in block_short_id.short_ids:
            struct.pack_into("<L", buffer, off, short_id)
            off += UL_INT_SIZE_IN_BYTES

    return buffer


def deserialize_blocks_short_ids_from_buffer(
    buffer: Union[bytearray, memoryview], offset: int, block_count: int
) -> List[BlockShortIds]:
    """
    Deserialize list of block short ids from buffer

    :param buffer: buffer containing serialized short ids bytes
    :param offset: offset in a buffer where serialized short ids begin
    :param block_count: how many blocks to deserialize
    :return: list of block short ids
    """
    block_short_ids: List[BlockShortIds] = []

    for _ in range(block_count):
        block_hash = Sha256Hash(buffer[offset:offset + SHA256_HASH_LEN])
        offset += SHA256_HASH_LEN
        short_ids_count, = struct.unpack_from("<L", buffer, offset)
        offset += UL_INT_SIZE_IN_BYTES
        short_ids = []
        for _ in range(short_ids_count):
            short_id, = struct.unpack_from("<L", buffer, offset)
            short_ids.append(short_id)
            offset += UL_INT_SIZE_IN_BYTES

        block_short_ids.append(BlockShortIds(block_hash, short_ids))

    return block_short_ids
