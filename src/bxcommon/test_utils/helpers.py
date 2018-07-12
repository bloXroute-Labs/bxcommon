import os

def generate_bytearray(size):
    result = bytearray(0)
    result.extend(os.urandom(size))

    return result
