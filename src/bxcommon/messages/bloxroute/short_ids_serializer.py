import struct
from typing import List, Tuple, Union

from bxcommon import constants


def get_serialized_length(count: int) -> int:
    return constants.UL_INT_SIZE_IN_BYTES + (count * constants.UL_INT_SIZE_IN_BYTES)


def serialize_short_ids_to_buffer(short_ids: List[int], buffer: bytearray, offset: int = 0) -> int:
    struct.pack_into("<L", buffer, offset, len(short_ids))
    offset += constants.UL_INT_SIZE_IN_BYTES

    for short_id in short_ids:
        struct.pack_into("<L", buffer, offset, short_id)
        offset += constants.UL_INT_SIZE_IN_BYTES

    return offset


def serialize_short_ids(short_ids: List[int]) -> bytearray:
    serialized_bytes = bytearray(get_serialized_length(len(short_ids)))
    serialize_short_ids_to_buffer(short_ids, serialized_bytes, 0)
    return serialized_bytes


def deserialize_short_ids_from_buffer(buffer: Union[bytearray, memoryview], offset: int = 0) -> Tuple[List[int], int]:
    short_ids = []

    short_ids_count, = struct.unpack_from("<L", buffer, offset)
    offset += constants.UL_INT_SIZE_IN_BYTES

    for _ in range(short_ids_count):
        short_id, = struct.unpack_from("<L", buffer, offset)
        short_ids.append(short_id)
        offset += constants.UL_INT_SIZE_IN_BYTES

    return short_ids, offset


def deserialize_short_ids(buffer: Union[bytearray, memoryview]) -> List[int]:
    short_ids, _ = deserialize_short_ids_from_buffer(buffer, 0)
    return short_ids
