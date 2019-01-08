def str_to_bool(value):
    return value in ["True", "true", "1"]

def bytes_to_hex(s):
    """
    Encodes bytes to hex

    :param s: bytes
    :return: HEX representation of bytes
    """

    if isinstance(s, bytearray):
        s = str(s)
    if isinstance(s, memoryview):
        s = str(s.tobytes())
    if not isinstance(s, (str, unicode)):
        raise TypeError("Value must be an instance of str or unicode")
    return s.encode("hex")

def hex_to_bytes(s):
    """
    Decodes hex string to bytes

    :param s: hex string
    :return: bytes
    """

    if not isinstance(s, (str, unicode)):
        raise TypeError("Value must be an instance of str or unicode")

    return s.decode("hex")
