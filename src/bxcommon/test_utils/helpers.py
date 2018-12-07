import os
import socket
from argparse import Namespace
from contextlib import closing

from mock import MagicMock

from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.constants import DEFAULT_NETWORK_NUM
from bxcommon.network.socket_connection import SocketConnection
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils.buffers.input_buffer import InputBuffer


def generate_bytearray(size):
    result = bytearray(0)
    result.extend(os.urandom(size))

    return result


def create_connection(connection_cls):
    if not issubclass(connection_cls, AbstractConnection):
        raise TypeError("{0} is not a subclass of AbstractConnection".format(connection_cls))

    test_address = ('0.0.0.0', 8001)
    test_socket = MagicMock(spec=socket.socket)
    mock_node = MockNode('0.0.0.0', 8002)
    test_socket_connection = SocketConnection(test_socket, mock_node)
    connection = connection_cls(test_socket_connection, test_address, mock_node)
    connection.idx = 1

    return connection


def get_free_port():
    """
    Find a free port and returns it. Has a race condition that some other process could steal the port between this
    and the actual port usage, but that shouldn't be too important.
    :return: port number
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))
        address, port = sock.getsockname()
    return port


def create_input_buffer_with_message(message):
    return create_input_buffer_with_bytes(message.rawbytes())


def create_input_buffer_with_bytes(message_bytes):
    input_buffer = InputBuffer()
    input_buffer.add_bytes(message_bytes)
    return input_buffer


def get_gateway_opts(port, node_id=None, external_ip="127.0.0.1", internal_ip="0.0.0.0", blockchain_address=None,
                     test_mode="", peer_gateways=None, peer_relays=None, protocol_version=1, sid_expire_time=30,
                     bloxroute_version="bloxroute 1.5", include_default_btc_args=False, include_default_etc_args=False,
                     network_num=DEFAULT_NETWORK_NUM, min_peer_gateways=0, **kwargs):
    if node_id is None:
        node_id = "Gateway at {0}".format(port)
    if peer_gateways is None:
        peer_gateways = []
    if peer_relays is None:
        peer_relays = []
    if blockchain_address is None:
        blockchain_address = ("127.0.0.1", 7000)  # not real, just a placeholder
    opts = Namespace()
    opts.__dict__ = {
        "node_id": node_id,
        "sid_expire_time": sid_expire_time,
        "bloxroute_version": bloxroute_version,
        "external_ip": external_ip,
        "external_port": port,
        "internal_ip": internal_ip,
        "internal_port": port,
        "blockchain_ip": blockchain_address[0],
        "blockchain_port": blockchain_address[1],
        "test_mode": test_mode,
        "peer_gateways": peer_gateways,
        "peer_relays": peer_relays,
        "outbound_peers": peer_gateways + peer_relays,
        "protocol_version": protocol_version,
        "network_num": network_num,
        "min_peer_gateways": min_peer_gateways
    }
    if include_default_btc_args:
        opts.__dict__.update({
            "blockchain_net_magic": 12345,
            "blockchain_version": 23456,
            "blockchain_nonce": 0,
            "blockchain_services": 1,
        })
    if include_default_etc_args:
        opts.__dict__.update({
            "private_key": "294549f8629f0eeb2b8e01aca491f701f5386a9662403b485c4efe7d447dfba3",
            "network_id": 1,
            "chain_difficulty": 4194304,
            "genesis_hash": "1e8ff5fd9d06ab673db775cf5c72a6b2d63171cd26fe1e6a8b9d2d696049c781",
            "no_discovery": True,
        })
    for key, val in kwargs.items():
        opts.__dict__[key] = val
    return opts


SID_SIZE = 100 * 1000 * 1000


def get_relay_opts(index, port, relay_addresses=None):
    if relay_addresses is None:
        relay_addresses = []
    opts = Namespace()
    opts.__dict__ = {
        "node_id": "Relay {0}".format(index),
        "external_ip": "127.0.0.1",
        "external_port": port,
        "internal_ip": "0.0.0.0",
        "internal_port": port,
        "sid_start": index * SID_SIZE + 1,
        "sid_end": (index + 1) * SID_SIZE,  # tx_service is inclusive
        "sid_expire_time": 30,
        "outbound_peers": relay_addresses,
        "idx": index,
        "test_mode": "",
    }
    return opts
