import argparse
import os
import sys
from argparse import ArgumentParser
from typing import List, Optional, Union

from bxcommon import constants
from bxcommon.constants import ALL_NETWORK_NUM
from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.models.node_type import NodeType
from bxcommon.rpc import rpc_constants
from bxcommon.services import http_service
from bxcommon.services import sdn_http_service
from bxcommon.utils import config, ip_resolver, convert, node_cache
from bxcommon.utils.node_start_args import NodeStartArgs
from bxutils import constants as utils_constants
from bxutils import log_messages
from bxutils import logging
from bxutils.logging import log_config
from bxutils.logging.log_format import LogFormat
from bxutils.logging.log_level import LogLevel

logger = logging.get_logger(__name__)


def get_argument_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser(add_help=False)

    arg_parser.add_argument("--external-ip", help="External network ip of this node",
                            type=ip_resolver.blocking_resolve_ip)
    arg_parser.add_argument("--external-port", help="External network port to listen on", type=int,
                            default=config.get_env_default(NodeStartArgs.EXTERNAL_PORT))
    arg_parser.add_argument("--non-ssl-port", help="External network port for non SSL nodes to listen on", type=int,
                            default=config.get_env_default(NodeStartArgs.NON_SSL_PORT))
    arg_parser.add_argument("--continent", help="The continent of this node", type=str,
                            choices=["NA", "SA", "EU", "AS", "AF", "OC", "AN"])
    arg_parser.add_argument("--country", help="The country of this node.", type=str)
    arg_parser.add_argument("--region", help="The region of this node.", type=str)
    arg_parser.add_argument("--hostname", help="Hostname the node is running on", type=str,
                            default=constants.HOSTNAME)
    arg_parser.add_argument("--sdn-url", help="IP or dns of the bloxroute SDN", type=str,
                            default=config.get_env_default(NodeStartArgs.SDN_ROOT_URL))
    arg_parser.add_argument(
        "--node-id",
        help="(TEST ONLY) Set the node_id for using in testing."
    )
    arg_parser.add_argument("--transaction-pool-memory-limit",
                            help="Maximum size of transactions to keep in memory pool (MB)",
                            type=int)

    arg_parser.add_argument("--info-stats-interval",
                            help="Frequency of info statistics logs in seconds",
                            type=int,
                            default=constants.INFO_STATS_INTERVAL_S)

    arg_parser.add_argument("--throughput-stats-interval",
                            help="Frequency of throughput statistics logs in seconds",
                            type=int,
                            default=constants.THROUGHPUT_STATS_INTERVAL_S)

    arg_parser.add_argument("--memory-stats-interval",
                            help="Frequency of memory statistics logs in seconds",
                            type=int,
                            default=constants.MEMORY_STATS_INTERVAL_S)

    arg_parser.add_argument("--dump-detailed-report-at-memory-usage",
                            help="Total memory usage of application when detailed memory report "
                                 "should be dumped to log (MB)",
                            type=int,
                            default=(2 * 1024))
    arg_parser.add_argument("--dump-removed-short-ids",
                            help="Dump removed short ids to a file at a fixed interval",
                            type=convert.str_to_bool,
                            default=False)
    arg_parser.add_argument("--dump-removed-short-ids-path",
                            help="Folder to dump removed short ids to",
                            type=str,
                            default=constants.DUMP_REMOVED_SHORT_IDS_PATH)
    arg_parser.add_argument("--enable-buffered-send", help="Enables buffering of sent byte to improve performance",
                            type=convert.str_to_bool, default=False)
    arg_parser.add_argument("--track-detailed-sent-messages", help="Enables tracking of messages written on socket",
                            type=convert.str_to_bool, default=False)
    arg_parser.add_argument(
        "--use-extensions",
        help="If true than the node will use the extension module for "
             "some tasks like block compression (default: {0})".format(constants.USE_EXTENSION_MODULES),
        default=constants.USE_EXTENSION_MODULES,
        type=convert.str_to_bool
    )

    arg_parser.add_argument(
        "--import-extensions",
        help="If true than the node will import all C++ extensions dependencies on start up",
        default=False,
        type=convert.str_to_bool
    )
    arg_parser.add_argument(
        "--thread-pool-parallelism-degree",
        help="The degree of parallelism to use when running task on a "
        f"concurrent thread pool (default: {constants.DEFAULT_THREAD_POOL_PARALLELISM_DEGREE})",
        default=constants.DEFAULT_THREAD_POOL_PARALLELISM_DEGREE,
        type=config.get_thread_pool_parallelism_degree
    )
    arg_parser.add_argument(
        "--tx-mem-pool-bucket-size",
        help="The size of each bucket of the transaction mem pool. "
             "In order to efficiently iterate the mem pool concurrently, it is being split into buckets. "
        f"(default: {constants.DEFAULT_TX_MEM_POOL_BUCKET_SIZE})",
        default=constants.DEFAULT_TX_MEM_POOL_BUCKET_SIZE,
        type=int
    )
    arg_parser.add_argument(
        "--sync-tx-service",
        help="sync tx service in node",
        type=convert.str_to_bool,
        default=True
    )
    arg_parser.add_argument(
        "--block-compression-debug",
        help="Enable debug messages with details of the compressed blocks",
        type=convert.str_to_bool,
        default=True
    )
    arg_parser.add_argument(
        "--enable-tcp-quickack",
        help="Enable TCP_QUICKACK so that ACK's are not delayed",
        type=convert.str_to_bool,
        default=True
    )

    add_argument_parser_logging(arg_parser)
    add_argument_parser_common(arg_parser)
    return arg_parser


def add_argument_parser_rpc(
    arg_parser: ArgumentParser,
    default_rpc_host=rpc_constants.DEFAULT_RPC_HOST,
    default_rpc_port=rpc_constants.DEFAULT_RPC_PORT
):
    arg_parser.add_argument(
        "--rpc",
        help="Start a HTTP(S) JSON-RPC server",
        type=convert.str_to_bool,
        default=True
    )
    arg_parser.add_argument(
        "--rpc-host",
        help="The node RPC host (default: {}).".format(rpc_constants.DEFAULT_RPC_HOST),
        type=str,
        default=default_rpc_host
    )
    arg_parser.add_argument(
        "--rpc-port",
        help="The node RPC port (default: {}).".format(rpc_constants.DEFAULT_RPC_PORT),
        type=int,
        default=default_rpc_port,
    )
    arg_parser.add_argument(
        "--rpc-use-ssl",
        help="Use secured communication (HTTPS, WSS)",
        type=convert.str_to_bool,
        default=False,
    )
    arg_parser.add_argument(
        "--rpc-ssl-base-url",
        help="The base url for ca, cert, and key used by the RPC server",
        type=str,
        default=rpc_constants.DEFAULT_RPC_BASE_SSL_URL,
    )
    arg_parser.add_argument(
        "--rpc-user",
        help=f"The node RPC server user (default: {rpc_constants.DEFAULT_RPC_USER})",
        type=str,
        default=rpc_constants.DEFAULT_RPC_USER,
    )
    arg_parser.add_argument(
        "--rpc-password",
        help=f"The node RPC server password (default: {rpc_constants.DEFAULT_RPC_PASSWORD})",
        type=str,
        default=rpc_constants.DEFAULT_RPC_PASSWORD,
    )


def add_argument_parser_logging(
    arg_parser: ArgumentParser,
    default_log_level: Union[LogLevel, str] = utils_constants.DEFAULT_LOG_LEVEL
):
    default_log_level = os.environ.get("LOG_LEVEL", default_log_level)
    default_log_format = os.environ.get("LOG_FORMAT", utils_constants.DEFAULT_LOG_FORMAT)
    default_log_fluentd_enable = os.environ.get("LOG_FLUENTD_ENABLE", False)
    default_log_fluentd_host = os.environ.get("LOG_FLUENTD_HOST", utils_constants.FLUENTD_HOST)
    default_fluentd_logger_max_queue_size = os.environ.get(
        "FLUENTD_LOGGER_MAX_QUEUE_SIZE", utils_constants.FLUENTD_LOGGER_MAX_QUEUE_SIZE
    )
    default_log_level_overrides = os.environ.get("LOG_LEVEL_OVERRIDES", {})
    default_log_level_fluentd = os.environ.get("LOG_LEVEL_FLUENTD", LogLevel.NOTSET)
    default_log_level_stdout = os.environ.get("LOG_LEVEL_STDOUT", LogLevel.NOTSET)

    arg_parser.add_argument(
        "--log-level",
        help="set log level",
        # pyre-fixme[16]: `LogLevel` has no attribute `__getattr__`.
        type=LogLevel.__getattr__,
        choices=list(LogLevel),
        default=default_log_level
    )
    arg_parser.add_argument(
        "--log-format",
        help="set log format",
        # pyre-fixme[16]: `LogFormat` has no attribute `__getattr__`.
        type=LogFormat.__getattr__,
        choices=list(LogFormat),
        default=default_log_format
    )
    arg_parser.add_argument(
        "--log-fluentd-enable",
        help="enable logging directly to fluentd",
        type=convert.str_to_bool,
        default=default_log_fluentd_enable
    )
    arg_parser.add_argument(
        "--log-fluentd-host",
        help="fluentd instance address provide, hostname:port",
        type=str,
        default=default_log_fluentd_host
    )
    arg_parser.add_argument(
        "--log-fluentd-queue-size",
        help="fluentd queue size",
        type=int,
        default=default_fluentd_logger_max_queue_size
    )
    arg_parser.add_argument(
        "--log-flush-immediately",
        help="Enables immediate flush for logs",
        type=convert.str_to_bool,
        default=False
    )
    arg_parser.add_argument(
        "--log-level-overrides",
        help="override log level for namespace stats=INFO,bxcommon.connections=WARNING",
        default=default_log_level_overrides,
        type=log_config.str_to_log_options
    )
    arg_parser.add_argument(
        "--log-level-fluentd",
        help="The fluentd handler log level",
        type=LogLevel.__getattr__,
        choices=list(LogLevel),
        default=default_log_level_fluentd
    )
    arg_parser.add_argument(
        "--log-level-stdout",
        help="The stdout handler log level",
        type=LogLevel.__getattr__,
        choices=list(LogLevel),
        default=default_log_level_stdout
    )
    arg_parser.add_argument(
        "--transaction-validation",
        help="Enable transaction validation process",
        type=convert.str_to_bool,
        default=True
    )


def add_argument_parser_common(arg_parser: ArgumentParser):
    arg_parser.add_argument(
        "--data-dir",
        help="Path to store configuration, state and log files",
        default=config.get_default_data_path()
    )
    arg_parser.add_argument(
        "--ca-cert-url",
        help="The URL for retrieving BDN ca certificate data (default: {})".format(
            config.get_env_default(NodeStartArgs.CA_CERT_URL)
        ),
        default=config.get_env_default(NodeStartArgs.CA_CERT_URL),
        type=str
    )
    arg_parser.add_argument(
        "--private-ssl-base-url",
        help="The base URL for retrieving specific certificate data (default: {})".format(
            config.get_env_default(NodeStartArgs.PRIVATE_SSL_BASE_URL)
        ),
        default=config.get_env_default(NodeStartArgs.PRIVATE_SSL_BASE_URL),
        type=str
    )


def add_feed_source_arguments(arg_parser: argparse.ArgumentParser) -> None:
    arg_parser.add_argument("--source-feed-ip", help="Source feed ip", type=str)
    arg_parser.add_argument("--source-feed-port", help="Source feed port", type=int)
    arg_parser.add_argument("--source-feed-rpc-user", help="Source feed user", type=str)
    arg_parser.add_argument("--source-feed-rpc-password", help="Source feed pass", type=str)


def parse_arguments(arg_parser: argparse.ArgumentParser, args: Optional[List[str]] = None) -> argparse.Namespace:
    opts, _unknown = arg_parser.parse_known_args(args)
    if not opts.external_ip:
        opts.external_ip = ip_resolver.get_node_public_ip()
    assert opts.external_ip is not None
    opts.external_ip = ip_resolver.blocking_resolve_ip(opts.external_ip)
    http_service.set_root_url(opts.sdn_url)
    config.append_manifest_args(opts.__dict__)
    return opts


def parse_blockchain_opts(opts, node_type: NodeType):
    """
    Get the blockchain network info from the SDN and set the default values for the blockchain cli params if they were
    not passed in the args.

    :param opts: argument list
    :param node_type:
    """
    opts_dict = opts.__dict__

    if node_type in NodeType.RELAY or node_type in NodeType.BLOXROUTE_CLOUD_API:
        opts_dict["blockchain_network_num"] = ALL_NETWORK_NUM
        return

    network_info = _get_blockchain_network_info(opts)

    for key, value in opts_dict.items():
        if value is None and network_info.default_attributes is not None and key in network_info.default_attributes:
            opts_dict[key] = network_info.default_attributes[key]

    opts_dict["blockchain_network_num"] = network_info.network_num
    opts_dict["blockchain_block_interval"] = network_info.block_interval
    opts_dict["blockchain_ignore_block_interval_count"] = network_info.ignore_block_interval_count
    opts_dict["blockchain_block_recovery_timeout_s"] = network_info.block_recovery_timeout_s
    opts_dict["blockchain_block_hold_timeout_s"] = network_info.block_hold_timeout_s
    opts_dict["enable_network_content_logs"] = network_info.enable_network_content_logs

    if opts.enable_block_compression is None:
        opts_dict["enable_block_compression"] = network_info.enable_block_compression


def _set_blockchain_networks_from_cache(opts):
    cache_info = node_cache.read(opts)
    if cache_info:
        opts.blockchain_networks = cache_info.blockchain_networks
    if not opts.blockchain_networks:
        logger.warning(log_messages.EMPTY_BLOCKCHAIN_NETWORK_CACHE)


def set_blockchain_networks_info(opts):
    opts.blockchain_networks = sdn_http_service.fetch_blockchain_networks()
    if not opts.blockchain_networks:
        logger.warning(log_messages.EMPTY_BLOCKCHAIN_NETWORK_LIST)
        _set_blockchain_networks_from_cache(opts)


def _get_blockchain_network_info(opts) -> BlockchainNetworkModel:
    """
    Retrieves the blockchain network info from the SDN based on blockchain-protocol
    and blockchain-network cli arguments.

    :param opts: argument list
    """

    for blockchain_network in opts.blockchain_networks.values():
        if blockchain_network.protocol.lower() == opts.blockchain_protocol.lower() and \
                blockchain_network.network.lower() == opts.blockchain_network.lower():
            return blockchain_network

    blockchain_networks = opts.blockchain_networks
    cache_network_info = node_cache.read(opts)
    if not blockchain_networks and cache_network_info:
        blockchain_networks = cache_network_info.blockchain_networks

    if blockchain_networks:
        all_networks_names = "\n".join(
            map(lambda n: "{} - {}".format(n.protocol, n.network), blockchain_networks.values())
        )
        error_msg = "Network number does not exist for blockchain protocol {} and network {}.\nValid options:\n{}" \
            .format(opts.blockchain_protocol, opts.blockchain_network, all_networks_names)
        logger.fatal(error_msg, exc_info=False)
    else:
        logger.fatal("Could not reach the SDN to fetch network information. Check that {} is the actual address "
                     "you are trying to reach.", opts.sdn_url, exc_info=False)
    sys.exit(1)
