import time

FACTOR = pow(10, 6)


def get_nonce() -> int:
    """
    using timestamp to generate unique nonce values
    :return: int
    """
    return int(time.time() * FACTOR)


def get_timestamp_from_nonce(nonce: int) -> float:
    return nonce / FACTOR
