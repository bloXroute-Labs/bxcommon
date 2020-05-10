import argparse
import sys
from argparse import ArgumentParser
from argparse import Namespace
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Dict
from urllib.parse import urlparse

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


@dataclass()
class CommonOpts:
    external_ip: str
    external_port: int
    non_ssl_port: int
    continent: str
    country: str
    hostname: str
    sdn_url: str
    log_level: LogLevel
    log_format: LogFormat
    log_flush_immediately: bool
    log_level_overrides: Dict[str, LogLevel]
    log_fluentd_enable: bool
    log_fluentd_host: str
    node_id: str
    transaction_pool_memory_limit: int
    info_stats_interval: int
    throughput_stats_interval: int
    memory_stats_interval: int
    dump_detailed_report_at_memory_usage: int
    dump_removed_short_ids: bool
    dump_removed_short_ids_path: str
    enable_buffered_send: bool
    track_detailed_sent_messages: bool
    use_extensions: bool
    import_extensions: bool
    thread_pool_parallelism_degree: int
    tx_mem_pool_bucket_size: int
    protocol_version: int
    source_version: int
    ca_cert_url: str
    private_ssl_base_url: str
    log_fluentd_queue_size: int
    log_level_fluentd: LogLevel
    log_level_stdout: LogLevel

    def __init__(self, opts: Namespace):
        self.external_ip = opts.external_ip
        self.external_port = opts.external_port
        self.non_ssl_port = opts.non_ssl_port
        self.continent = opts.continent
        self.country = opts.country
        self.hostname = opts.hostname
        self.sdn_url = opts.sdn_url
        self.log_level = opts.log_level
        self.log_format = opts.log_format
        self.log_flush_immediately = opts.log_flush_immediately
        self.log_level_overrides = opts.log_level_overrides
        self.log_fluentd_enable = opts.log_fluentd_enable
        self.log_fluentd_host = opts.log_fluentd_host
        self.node_id = opts.node_id
        self.transaction_pool_memory_limit = opts.transaction_pool_memory_limit
        self.info_stats_interval = opts.info_stats_interval
        self.throughput_stats_interval = opts.throughput_stats_interval
        self.memory_stats_interval = opts.memory_stats_interval
        self.dump_detailed_report_at_memory_usage = opts.dump_detailed_report_at_memory_usage
        self.dump_removed_short_ids = opts.dump_removed_short_ids
        self.dump_removed_short_ids_path = opts.dump_removed_short_ids_path
        self.enable_buffered_send = opts.enable_buffered_send
        self.track_detailed_sent_messages = opts.track_detailed_sent_messages
        self.use_extensions = opts.use_extensions
        self.import_extensions = opts.import_extensions
        self.thread_pool_parallelism_degree = opts.thread_pool_parallelism_degree
        self.tx_mem_pool_bucket_size = opts.tx_mem_pool_bucket_size
        self.data_dir = opts.data_dir
        self.protocol_version = opts.protocol_version
        self.source_version = opts.source_version
        self.ca_cert_url = opts.ca_cert_url
        self.private_ssl_base_url = opts.private_ssl_base_url
        self.non_ssl_port = opts.non_ssl_port
        self.log_level_fluentd = opts.log_level_fluentd
        self.log_level_stdout = opts.log_level_stdout
        self.log_fluentd_queue_size = opts.log_fluentd_queue_size

        # Validation
        self.validate_external_ip()

    def validate_external_ip(self):
        parsed_sdn_url = urlparse(self.sdn_url)
        sdn_host = parsed_sdn_url.netloc.split(":")[0]
        sdn_ip = ip_address(ip_resolver.blocking_resolve_ip(sdn_host))
        if not sdn_ip.is_private and self.external_ip and ip_address(self.external_ip).is_private:
            logger.fatal(
                "The specified external IP ({}) is a known private IP address. Try omitting this argument",
                self.external_ip,
                exc_info=False
            )
            sys.exit(1)


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
    arg_parser.add_argument("--hostname", help="Hostname the node is running on", type=str,
                            default=constants.HOSTNAME)
    arg_parser.add_argument("--sdn-url", help="IP or dns of the bloxroute SDN", type=str,
                            default=config.get_env_default(NodeStartArgs.SDN_ROOT_URL))
    arg_parser.add_argument(
        "--node-id",
        help="(TEST ONLY) Set the node_id for using in testing."
    )

    arg_parser.add_argument(
        "--rpc-host",
        help="The node RPC host (default: {}).".format(rpc_constants.DEFAULT_RPC_HOST),
        type=str,
        default=rpc_constants.DEFAULT_RPC_HOST
    )
    arg_parser.add_argument(
        "--rpc-port",
        help="The node RPC port (default: {}).".format(rpc_constants.DEFAULT_RPC_PORT),
        type=int,
        default=rpc_constants.DEFAULT_RPC_PORT
    )
    arg_parser.add_argument(
        "--rpc-user",
        help=f"The node RPC server user (default: {rpc_constants.DEFAULT_RPC_USER})",
        type=str,
        default=rpc_constants.DEFAULT_RPC_USER
    )
    arg_parser.add_argument(
        "--rpc-password",
        help=f"The node RPC server password (default: {rpc_constants.DEFAULT_RPC_PASSWORD})",
        type=str,
        default=rpc_constants.DEFAULT_RPC_PASSWORD
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

    add_argument_parser_logging(arg_parser)
    add_argument_parser_common(arg_parser)
    return arg_parser


def add_argument_parser_logging(arg_parser: ArgumentParser):
    arg_parser.add_argument(
        "--log-level",
        help="set log level",
        # pyre-fixme[16]: `LogLevel` has no attribute `__getattr__`.
        type=LogLevel.__getattr__,
        choices=list(LogLevel),
        default=utils_constants.DEFAULT_LOG_LEVEL
    )
    arg_parser.add_argument(
        "--log-format",
        help="set log format",
        # pyre-fixme[16]: `LogFormat` has no attribute `__getattr__`.
        type=LogFormat.__getattr__,
        choices=list(LogFormat),
        default=utils_constants.DEFAULT_LOG_FORMAT
    )
    arg_parser.add_argument(
        "--log-fluentd-enable",
        help="enable logging directly to fluentd",
        type=convert.str_to_bool,
        default=False
    )
    arg_parser.add_argument(
        "--log-fluentd-host",
        help="fluentd instance address provide, hostname:port",
        type=str,
        default=utils_constants.FLUENTD_HOST
    )
    arg_parser.add_argument(
        "--log-fluentd-queue-size",
        help="fluentd queue size",
        type=int,
        default=utils_constants.FLUENTD_LOGGER_MAX_QUEUE_SIZE
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
        default={},
        type=log_config.str_to_log_options
    )
    arg_parser.add_argument(
        "--log-level-fluentd",
        help="The fluentd handler log level",
        type=LogLevel.__getattr__,
        choices=list(LogLevel),
        default=LogLevel.NOTSET
    )
    arg_parser.add_argument(
        "--log-level-stdout",
        help="The stdout handler log level",
        type=LogLevel.__getattr__,
        choices=list(LogLevel),
        default=LogLevel.NOTSET
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


def parse_arguments(arg_parser: argparse.ArgumentParser) -> argparse.Namespace:
    opts, _unknown = arg_parser.parse_known_args()
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

    if node_type in NodeType.RELAY or node_type in NodeType.BLOXROUTE_PUBLIC_API:
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


def _set_blockchain_networks_from_cache(opts):
    cache_info = node_cache.read(opts)
    if cache_info:
        opts.blockchain_networks = cache_info.blockchain_network
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

    for blockchain_network in opts.blockchain_networks:
        if blockchain_network.protocol.lower() == opts.blockchain_protocol.lower() and \
                blockchain_network.network.lower() == opts.blockchain_network.lower():
            return blockchain_network

    if opts.blockchain_networks:
        all_networks_names = "\n".join(
            map(lambda n: "{} - {}".format(n.protocol, n.network), opts.blockchain_networks))
        error_msg = "Network number does not exist for blockchain protocol {} and network {}.\nValid options:\n{}" \
            .format(opts.blockchain_protocol, opts.blockchain_network, all_networks_names)
        logger.fatal(error_msg, exc_info=False)
    else:
        logger.fatal("Could not reach the SDN to fetch network information. Check that {} is the actual address "
                     "you are trying to reach.", opts.sdn_url, exc_info=False)
    sys.exit(1)


def set_os_version(opts):
    opts.__dict__["os_version"] = constants.OS_VERSION
