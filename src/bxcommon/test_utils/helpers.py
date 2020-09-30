import asyncio
import os
import socket
import sys
import uuid
from argparse import Namespace
from contextlib import closing
from typing import Optional, TypeVar, Type, TYPE_CHECKING, List

from mock import MagicMock

from bxcommon import constants
from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.models.authenticated_peer_info import AuthenticatedPeerInfo
from bxcommon.models.blockchain_network_environment import BlockchainNetworkEnvironment
from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.models.blockchain_network_type import BlockchainNetworkType
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.network.network_direction import NetworkDirection
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.test_utils.mocks.mock_socket_connection import MockSocketConnection
from bxcommon.utils import config, crypto, convert
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.common_opts import CommonOpts
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.utils.proxy import task_pool_proxy
from bxutils.logging.log_format import LogFormat
from bxutils.logging.log_level import LogLevel
from bxutils import constants as utils_constants

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports
    from bxcommon.connections.abstract_connection import AbstractConnection


COOKIE_FILE_PATH = "gateway_cookies/.cookie.blxrbdn-gw-localhost:8080"
BTC_COMPACT_BLOCK_DECOMPRESS_MIN_TX_COUNT = 10


def generate_bytes(size):
    return bytes(generate_bytearray(size))


def generate_bytearray(size):
    result = bytearray(0)
    result.extend(os.urandom(size))

    return result


def generate_hash() -> bytearray:
    return generate_bytearray(crypto.SHA256_HASH_LEN)


def generate_object_hash() -> Sha256Hash:
    return Sha256Hash(generate_hash())


def generate_node_id() -> str:
    return str(uuid.uuid4())


Connection = TypeVar("Connection", bound="AbstractConnection")


def create_connection(
    connection_cls: Type[Connection],
    node: Optional[AbstractNode] = None,
    node_opts: Optional[CommonOpts] = None,
    file_no: int = 1,
    ip: str = constants.LOCALHOST,
    port: int = 8001,
    from_me: bool = False,
    add_to_pool: bool = True,
    authentication_info: Optional[AuthenticatedPeerInfo] = None
) -> Connection:
    if node_opts is None:
        node_opts = get_common_opts(8002)

    if node is None:
        node = MockNode(node_opts, None)

    if authentication_info is None:
        authentication_info = AuthenticatedPeerInfo(
            connection_cls.CONNECTION_TYPE,
            node_opts.node_id,
            ""
        )

    if isinstance(node, MockNode):
        add_to_pool = False

    test_socket_connection = MockSocketConnection(file_no, node, ip_address=ip, port=port)
    if not from_me:
        test_socket_connection.direction = NetworkDirection.INBOUND
    connection = connection_cls(test_socket_connection, node)

    connection.on_connection_authenticated(authentication_info)

    if add_to_pool:
        node.connection_pool.add(file_no, ip, port, connection)
    return connection


def clear_node_buffer(node, fileno):
    bytes_to_send = node.get_bytes_to_send(fileno)
    while bytes_to_send is not None and len(bytes_to_send) > 0:
        node.on_bytes_sent(fileno, len(bytes_to_send))
        bytes_to_send = node.get_bytes_to_send(fileno)


def receive_node_message(node, fileno, message):
    node.on_bytes_received(fileno, message)


def get_queued_node_bytes(
    node: AbstractNode, fileno: int, message_type: bytes, flush: bool = True
) -> memoryview:
    bytes_to_send = node.get_bytes_to_send(fileno)
    assert bytes_to_send is not None
    assert message_type in bytes_to_send.tobytes(), (
        f"could not find {message_type} in message bytes "
        f"{convert.bytes_to_hex(bytes_to_send.tobytes())} "
        f"on file_no: {fileno}"
    )
    if flush:
        node.on_bytes_sent(fileno, len(bytes_to_send))
    return bytes_to_send


def get_queued_node_messages(node: AbstractNode, fileno: int) -> List[AbstractMessage]:
    connection = node.connection_pool.get_by_fileno(fileno)
    assert connection is not None
    assert connection.message_factory is not None
    bytes_to_send = node.get_bytes_to_send(fileno)
    input_buffer = create_input_buffer_with_bytes(bytes_to_send)

    total_bytes = 0
    messages = []
    (
        is_full_message,
        _message_type,
        payload_length,
    ) = connection.message_factory.get_message_header_preview_from_input_buffer(input_buffer)
    while is_full_message:
        message_length = connection.message_factory.base_message_type.HEADER_LENGTH + payload_length
        message_contents = input_buffer.remove_bytes(message_length)
        total_bytes += message_length

        messages.append(connection.message_factory.create_message_from_buffer(message_contents))
        (
            is_full_message,
            _message_type,
            payload_length,
        ) = connection.message_factory.get_message_header_preview_from_input_buffer(input_buffer)

    if total_bytes:
        node.on_bytes_sent(fileno, total_bytes)
    return messages


def has_no_queued_messages(node: AbstractNode, fileno: int) -> bool:
    return len(get_queued_node_messages(node, fileno)) == 0


def get_free_port():
    """
    Find a free port and returns it. Has a race condition that some other process could steal the port between this
    and the actual port usage, but that shouldn't be too important.
    :return: port number
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))
        _address, port = sock.getsockname()
    return port


def create_input_buffer_with_message(message):
    return create_input_buffer_with_bytes(message.rawbytes())


def create_input_buffer_with_bytes(message_bytes):
    input_buffer = InputBuffer()
    input_buffer.add_bytes(message_bytes)
    return input_buffer


def set_extensions_parallelism(
    degree: int = constants.DEFAULT_THREAD_POOL_PARALLELISM_DEGREE,
) -> None:
    task_pool_proxy.init(config.get_thread_pool_parallelism_degree(str(degree)))


def blockchain_network(
    protocol: str,
    network_name: str,
    network_num: int,
    block_recovery_timeout: int = 30,
    block_hold_timeout: int = 30,
    final_tx_confirmations_count: int = 2,
    block_confirmations_count: int = 1,
    **kwargs,
) -> BlockchainNetworkModel:
    _blockchain_network = BlockchainNetworkModel(
        protocol,
        network_name,
        network_num,
        BlockchainNetworkType.PUBLIC,
        BlockchainNetworkEnvironment.DEVELOPMENT,
        {},
        60,
        5,
        block_recovery_timeout,
        block_hold_timeout,
        final_tx_confirmations_count,
        50 * 1024 * 1024,
        block_confirmations_count=block_confirmations_count,
    )

    for key, val in kwargs.items():
        _blockchain_network.__dict__[key] = val
    return _blockchain_network


def get_common_opts(
    port: int,
    external_ip: str = constants.LOCALHOST,
    node_id: Optional[str] = None,
    outbound_peers: Optional[List[OutboundPeerModel]] = None,
    blockchain_network_num: int = constants.ALL_NETWORK_NUM,
    block_confirmations_count: int = 2,
    final_tx_confirmations_count: int = 4,
    rpc_port: int = 28332,
    continent: str = "NA",
    country: str = "United States",
    region: str = "us-east-1",
    parallelism_degree: int = 1,
    split_relays: bool = False,
    sid_expire_time: int = 30,
    rpc: bool = False,
    transaction_validation: bool = True,
    **kwargs,
) -> CommonOpts:
    if node_id is None:
        node_id = f"Node at {port}"
    if outbound_peers is None:
        outbound_peers = []

    opts = Namespace()
    opts.__dict__ = {
        "external_ip": external_ip,
        "external_port": port,
        "node_id": node_id,
        "memory_stats_interval": 3600,
        "dump_detailed_report_at_memory_usage": 100,
        "dump_removed_short_ids": False,
        "dump_removed_short_ids_path": "",
        "transaction_pool_memory_limit": 200000000,
        "track_detailed_sent_messages": True,
        "use_extensions": constants.USE_EXTENSION_MODULES,
        "import_extensions": constants.USE_EXTENSION_MODULES,
        "tx_mem_pool_bucket_size": constants.DEFAULT_TX_MEM_POOL_BUCKET_SIZE,
        "throughput_stats_interval": constants.THROUGHPUT_STATS_INTERVAL_S,
        "info_stats_interval": constants.INFO_STATS_INTERVAL_S,
        "sync_tx_service": True,
        "source_version": "v1.0.0",
        "non_ssl_port": 3000,
        "enable_node_cache": True,
        "rpc_port": rpc_port,
        "rpc_host": constants.LOCALHOST,
        "rpc_user": "",
        "rpc_password": "",
        "continent": continent,
        "country": country,
        "region": region,
        "hostname": "bxlocal",
        "sdn_url": f"{constants.LOCALHOST}:8080",
        "log_level": LogLevel.DEBUG,
        "log_format": LogFormat.PLAIN,
        "log_fluentd_queue_size": 1000,
        "log_level_fluentd": LogLevel.DEBUG,
        "log_level_stdout": LogLevel.TRACE,
        "log_level_overrides": {},
        "log_flush_immediately": True,
        "log_fluentd_enable": False,
        "log_fluentd_host": utils_constants.FLUENTD_HOST,
        "enable_buffered_send": False,
        "block_compression_debug": False,
        "enable_tcp_quickack": True,
        "thread_pool_parallelism_degree": config.get_thread_pool_parallelism_degree(
            str(parallelism_degree)
        ),
        "data_dir": config.get_default_data_path(),
        "ca_cert_url": "https://certificates.blxrbdn.com/ca",
        "private_ssl_base_url": "https://certificates.blxrbdn.com",
        "rpc": rpc,
        "transaction_validation": transaction_validation,
    }
    for key, val in kwargs.items():
        opts.__dict__[key] = val
    common_opts = CommonOpts.from_opts(opts)

    # some attributes are usually set by the node runner
    common_opts.__dict__.update({
        "node_type": AbstractNode.NODE_TYPE,
        "outbound_peers": outbound_peers,
        "sid_expire_time": sid_expire_time,
        "split_relays": split_relays,
        "blockchain_networks": {
            0: blockchain_network(
                "Bitcoin",
                "Mainnet",
                0,
                15,
                15,
                final_tx_confirmations_count,
                block_confirmations_count,
                ),
            1: blockchain_network(
                "Bitcoin",
                "Testnet",
                1,
                15,
                15,
                final_tx_confirmations_count,
                block_confirmations_count,
                ),
            4: blockchain_network(
                "BitcoinCash",
                "Testnet",
                4,
                15,
                15,
                24,
                block_confirmations_count,
            ),
            5: blockchain_network(
                "Ethereum",
                "Mainnet",
                5,
                5,
                5,
                24,
                block_confirmations_count,
            ),
            3: blockchain_network(
                "Ethereum",
                "Testnet",
                3,
                5,
                5,
                final_tx_confirmations_count,
                block_confirmations_count,
            ),
            33: blockchain_network(
                "Ontology",
                "Mainnet",
                33,
                5,
                5,
                final_tx_confirmations_count,
                block_confirmations_count,
            ),
        },
        "blockchain_network_num": blockchain_network_num,
    })
    return common_opts


# if an async test takes longer than 1s, assume it has failed
ASYNC_TEST_TIMEOUT_S: Optional[int] = 1
LONG_ASYNC_TEST_TIMEOUT_S: Optional[int] = 3

# do not trigger this if debugger is running
get_trace = getattr(sys, "gettrace", None)
if get_trace is not None and get_trace():
    ASYNC_TEST_TIMEOUT_S = None


def async_test(*args):
    timeout = ASYNC_TEST_TIMEOUT_S

    def _async_test(method):
        def wrapper(*args, **kwargs):
            async def async_method(*args, **kwargs):
                await method(*args, **kwargs)

            future = async_method(*args, **kwargs)
            task = asyncio.wait_for(future, timeout=timeout)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(task)
        return wrapper

    if len(args) == 1 and callable(args[0]):
        return _async_test(args[0])
    else:
        assert len(args) == 1
        timeout = args[0]
        return _async_test


class AsyncMock:
    mock: MagicMock

    def __init__(self, *args, **kwargs) -> None:
        self.mock = MagicMock(*args, **kwargs)

    async def __call__(self, *args, **kwargs):
        return self.mock(*args, **kwargs)
