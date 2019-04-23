import os
import socket
from argparse import Namespace
from contextlib import closing

from mock import MagicMock

from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.node_type import NodeType
from bxcommon.constants import DEFAULT_NETWORK_NUM, LOCALHOST, ALL_NETWORK_NUM, USE_EXTENSION_MODULES
from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.network.socket_connection import SocketConnection
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils.buffers.input_buffer import InputBuffer


def generate_bytes(size):
    return bytes(generate_bytearray(size))


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


def clear_node_buffer(node, fileno):
    bytes_to_send = node.get_bytes_to_send(fileno)
    while bytes_to_send is not None and len(bytes_to_send) > 0:
        node.on_bytes_sent(fileno, len(bytes_to_send))
        bytes_to_send = node.get_bytes_to_send(fileno)


def receive_node_message(node, fileno, message):
    node.on_bytes_received(fileno, message)
    node.on_finished_receiving(fileno)


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


def get_gateway_opts(port, node_id=None, external_ip=LOCALHOST, internal_ip="0.0.0.0", blockchain_address=None,
                     test_mode=None, peer_gateways=None, peer_relays=None, protocol_version=1, sid_expire_time=30,
                     bloxroute_version="bloxroute 1.5", include_default_btc_args=False, include_default_eth_args=False,
                     blockchain_network_num=DEFAULT_NETWORK_NUM, min_peer_gateways=0, remote_blockchain_ip=None,
                     remote_blockchain_port=None, connect_to_remote_blockchain=False, is_internal_gateway=False,
                     is_gateway_miner=False, **kwargs):
    if node_id is None:
        node_id = "Gateway at {0}".format(port)
    if peer_gateways is None:
        peer_gateways = []
    if peer_relays is None:
        peer_relays = []
    if blockchain_address is None:
        blockchain_address = ("127.0.0.1", 7000)  # not real, just a placeholder
    if test_mode is None:
        test_mode = []
    if remote_blockchain_ip is not None and remote_blockchain_port is not None:
        remote_blockchain_peer = (remote_blockchain_ip, remote_blockchain_port)
    else:
        remote_blockchain_peer = None
    opts = Namespace()
    opts.__dict__ = {
        "node_id": node_id,
        "node_type": NodeType.GATEWAY,
        "sid_expire_time": sid_expire_time,
        "bloxroute_version": bloxroute_version,
        "external_ip": external_ip,
        "external_port": port,
        "internal_ip": internal_ip,
        "internal_port": port,
        "blockchain_ip": blockchain_address[0],
        "blockchain_port": blockchain_address[1],
        "blockchain_protocol": "Bitcoin",
        "blockchain_network": "Mainnet",
        "test_mode": test_mode,
        "peer_gateways": peer_gateways,
        "peer_relays": peer_relays,
        "outbound_peers": peer_gateways + peer_relays,
        "protocol_version": protocol_version,
        "blockchain_network_num": blockchain_network_num,
        "blockchain_block_interval": 600,
        "blockchain_ignore_block_interval_count": 3,
        "min_peer_gateways": min_peer_gateways,
        "remote_blockchain_ip": remote_blockchain_ip,
        "remote_blockchain_port": remote_blockchain_port,
        "remote_blockchain_peer": remote_blockchain_peer,
        "connect_to_remote_blockchain": connect_to_remote_blockchain,
        "is_internal_gateway": is_internal_gateway,
        "is_gateway_miner": is_gateway_miner,
        "blockchain_networks": [
            BlockchainNetworkModel(protocol="Bitcoin", network="Mainnet", network_num=0, block_interval=600,
                                   final_tx_confirmations_count=6),
            BlockchainNetworkModel(protocol="Bitcoin", network="Testnet", network_num=1, block_interval=600,
                                   final_tx_confirmations_count=6),
            BlockchainNetworkModel(protocol="Ethereum", network="Mainnet", network_num=2, block_interval=15,
                                   final_tx_confirmations_count=3),
            BlockchainNetworkModel(protocol="Ethereum", network="Testnet", network_num=3, block_interval=15,
                                   final_tx_confirmations_count=3)
        ],
        "transaction_pool_memory_limit": 200000000,
        "encrypt_blocks": True,
        "use_extensions": USE_EXTENSION_MODULES,
        "import_extensions": USE_EXTENSION_MODULES
    }

    if include_default_btc_args:
        opts.__dict__.update({
            "blockchain_net_magic": 12345,
            "blockchain_version": 23456,
            "blockchain_nonce": 0,
            "blockchain_services": 1,
        })
    if include_default_eth_args:
        opts.__dict__.update({
            "private_key": "294549f8629f0eeb2b8e01aca491f701f5386a9662403b485c4efe7d447dfba3",
            "node_public_key": None,
            "remote_public_key": None,
            "network_id": 1,
            "chain_difficulty": 4194304,
            "genesis_hash": "1e8ff5fd9d06ab673db775cf5c72a6b2d63171cd26fe1e6a8b9d2d696049c781",
            "no_discovery": True,
        })
    for key, val in kwargs.items():
        opts.__dict__[key] = val
    return opts


SID_SIZE = 100 * 1000 * 1000


def get_relay_opts(index, port, external_ip=LOCALHOST, sdn_socket_ip=LOCALHOST, sdn_socket_port=8888,
                   relay_addresses=None, blockchain_network_num=ALL_NETWORK_NUM, sid_size=SID_SIZE,
                   sid_expire_time=1000):
    if relay_addresses is None:
        relay_addresses = []
    opts = Namespace()
    opts.__dict__ = {
        "node_id": "Relay {0}".format(index),
        "node_type": NodeType.RELAY,
        "external_ip": external_ip,
        "external_port": port,
        "internal_ip": "0.0.0.0",
        "internal_port": port,
        "sdn_socket_ip": sdn_socket_ip,
        "sdn_socket_port": sdn_socket_port,
        "sid_start": index * sid_size + 1,
        "sid_end": (index + 1) * sid_size,  # tx_service is inclusive
        "sid_expire_time": sid_expire_time,
        "outbound_peers": relay_addresses,
        "test_mode": "",
        "blockchain_network_num": blockchain_network_num,
        "blockchain_networks": [
            BlockchainNetworkModel(protocol="Bitcoin", network="Mainnet", network_num=0,
                                   final_tx_confirmations_count=2),
            BlockchainNetworkModel(protocol="Bitcoin", network="Testnet", network_num=1,
                                   final_tx_confirmations_count=2),
            BlockchainNetworkModel(protocol="Ethereum", network="Mainnet", network_num=2,
                                   final_tx_confirmations_count=2),
            BlockchainNetworkModel(protocol="Ethereum", network="Testnet", network_num=3,
                                   final_tx_confirmations_count=2)
        ],
        "transaction_pool_memory_limit": 200000000
    }
    return opts



