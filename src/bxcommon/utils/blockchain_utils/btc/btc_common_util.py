import struct
from hashlib import sha256
from typing import Union

from bxcommon.utils.blockchain_utils.btc import btc_common_constants
from bxcommon.utils.blockchain_utils.btc.btc_object_hash import BtcObjectHash


def btc_varint_to_int(buf, off):
    """
    Converts a varint to a regular integer in a buffer bytearray.
    https://en.bitcoin.it/wiki/Protocol_documentation#Variable_length_integer
    """
    if not isinstance(buf, memoryview):
        buf = memoryview(buf)

    if buf[off] == btc_common_constants.BTC_VARINT_LONG_INDICATOR:
        return struct.unpack_from("<Q", buf, off + 1)[0], 9
    elif buf[off] == btc_common_constants.BTC_VARINT_INT_INDICATOR:
        return struct.unpack_from("<I", buf, off + 1)[0], 5
    elif buf[off] == btc_common_constants.BTC_VARINT_SHORT_INDICATOR:
        return struct.unpack_from("<H", buf, off + 1)[0], 3
    else:
        return struct.unpack_from("B", buf, off)[0], 1


def is_segwit(buf: Union[memoryview, bytearray], off: int = 0) -> bool:
    """
    Determines if a transaction is a segwit transaction by reading the marker and flag bytes
    :param buf: the bytes of the transaction contents
    :param off: the desired offset
    :return: boolean indicating segwit
    """
    segwit_flag, = struct.unpack_from(">h", buf, off + btc_common_constants.TX_VERSION_LEN)
    return segwit_flag == btc_common_constants.TX_SEGWIT_FLAG_VALUE


def get_txid(buffer: Union[memoryview, bytearray]) -> BtcObjectHash:
    """
    Actually gets the txid, which is the same as the hash for non segwit transactions
    :param buffer: the bytes of the transaction contents
    :return: hash object
    """

    flag_len = btc_common_constants.TX_SEGWIT_FLAG_LEN if is_segwit(buffer) else 0
    txid = sha256(buffer[:btc_common_constants.TX_VERSION_LEN])
    end = btc_common_constants.TX_VERSION_LEN + flag_len
    io_size, _, _ = get_tx_io_count_and_size(buffer, end, tail=-1)
    txid.update(buffer[end:end + io_size])
    txid.update(buffer[-btc_common_constants.TX_LOCK_TIME_LEN:])

    return BtcObjectHash(buf=sha256(txid.digest()).digest(), length=btc_common_constants.BTC_SHA_HASH_LEN)


def get_tx_io_count_and_size(buf: Union[memoryview, bytearray], start, tail):
    end = start

    txin_c, size = btc_varint_to_int(buf, end)
    end += size

    if end > tail > 0:
        return -1

    for _ in range(txin_c):
        end += 36
        script_len, size = btc_varint_to_int(buf, end)
        end += size + script_len + 4

        if end > tail > 0:
            return -1

    txout_c, size = btc_varint_to_int(buf, end)
    end += size
    for _ in range(txout_c):
        end += 8
        script_len, size = btc_varint_to_int(buf, end)
        end += size + script_len

        if end > tail > 0:
            return -1

    return end - start, txin_c, txout_c
