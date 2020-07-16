import struct
from collections import namedtuple

from bxcommon import constants

BlockOffsets = namedtuple("BlockOffsets", ["short_id_offset", "block_begin_offset"])


def get_serialized_short_ids_bytes_len(short_ids) -> int:
    """
    Calculates length of list of short ids serialized into bytes

    :param short_ids: list of short ids
    :return: length of serialized bytes
    """

    return constants.UL_INT_SIZE_IN_BYTES + len(short_ids) * constants.UL_INT_SIZE_IN_BYTES


def serialize_short_ids_into_bytes(short_ids) -> bytearray:
    """
    Serializes short ids into bytes

    :param short_ids: list of short ids
    :return: bytearray with serialized bytes
    """

    buffer = bytearray(get_serialized_short_ids_bytes_len(short_ids))

    struct.pack_into("<L", buffer, 0, len(short_ids))
    offset = constants.UL_INT_SIZE_IN_BYTES

    for short_id in short_ids:
        struct.pack_into("<L", buffer, offset, short_id)
        offset += constants.UL_INT_SIZE_IN_BYTES

    return buffer


def deserialize_short_ids_from_buffer(buffer, offset):
    """
    Deserializes list of short ids from buffer

    :param buffer: buffer containing serialized short ids bytes
    :param offset: offset in a buffer where serialized short ids begin
    :return: list of short ids
    """

    short_ids_len, = struct.unpack_from("<L", buffer, offset)
    length = constants.UL_INT_SIZE_IN_BYTES

    short_ids = []

    for _ in range(short_ids_len):
        short_id, = struct.unpack_from("<L", buffer, offset + length)
        length += constants.UL_INT_SIZE_IN_BYTES
        short_ids.append(short_id)

    return short_ids, length


def get_bx_block_offsets(bx_block):
    short_id_offset, = struct.unpack_from("<Q", bx_block)
    return BlockOffsets(short_id_offset, constants.UL_ULL_SIZE_IN_BYTES)
