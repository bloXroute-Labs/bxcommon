import os
import socket

from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.test_utils.mocks.mock_node import MockNode


def generate_bytearray(size):
    result = bytearray(0)
    result.extend(os.urandom(size))

    return result


def create_connection(connection_cls):
    if not issubclass(connection_cls, AbstractConnection):
        raise TypeError("{0} is not a subclass of AbstractConnection".format(connection_cls))

    test_address = ('0.0.0.0', 8001)
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mock_node = MockNode('0.0.0.0', 8002)

    connection = connection_cls(test_socket, test_address, mock_node)
    connection.idx = 1

    return connection
