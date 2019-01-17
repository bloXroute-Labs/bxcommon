import time


def get_nonce():
    """
    using timestamp to generate unique nonce values
    :return: int
    """
    return int(time.time() * 1000 * 1000)
