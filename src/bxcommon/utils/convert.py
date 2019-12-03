import binascii
from binascii import Error


def str_to_bool(value):
    return value in ["True", "true", "1"]


def bytes_to_hex(s):
    """
    Encodes bytes to hex
    :param s: bytes
    :return: HEX representation of bytes
    """

    if not isinstance(s, (bytes, bytearray, memoryview)):
        raise TypeError("Value must be an instance of str")
    return binascii.hexlify(s).decode("utf-8")


def hex_to_bytes(s):
    """
    Decodes hex string to bytes
    :param s: hex string
    :return: bytes
    """

    if not isinstance(s, (str, bytes, bytearray, memoryview)):
        raise TypeError("Value must be an instance of str or unicode")
    try:
        return binascii.unhexlify(s)
    except Error as e:
        raise ValueError(f"Invalid hex string provided: {s}.") from e
