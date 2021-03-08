import base64
import ipaddress
import sys
import dataclasses

from typing import Dict, List, Set, Optional, Iterable
from dataclasses import dataclass

from datetime import datetime
from argparse import Namespace
from urllib import parse

from bxutils import logging
from bxutils.logging.log_level import LogLevel
from bxutils.logging.log_format import LogFormat
from bxutils.logging import LoggerConfig
from bxcommon.utils import ip_resolver

from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.models.bdn_account_model_base import BdnAccountModelBase
from bxcommon.models.node_type import NodeType

from bxcommon import constants


logger = logging.get_logger(__name__)


@dataclass()
class SourceFeedOpts:
    source_feed_ip: str
    source_feed_port: int
    source_feed_rpc_user: str
    source_feed_rpc_password: str

    def get_source_feed_auth(self) -> str:
        return base64.b64encode(
            f"{self.source_feed_rpc_user}:{self.source_feed_rpc_password}".encode("utf-8")
        ).decode("utf-8")


@dataclass
class CommonOpts:
    external_ip: str
    external_port: int
    non_ssl_port: int
    continent: str
    country: str
    region: str
    hostname: str
    sdn_url: str
    log_level: LogLevel
    log_format: LogFormat
    log_flush_immediately: bool
    log_level_overrides: Dict[str, LogLevel]
    log_fluentd_enable: bool
    log_fluentd_host: str
    node_id: str
    transaction_pool_memory_limit: float
    info_stats_interval: int
    throughput_stats_interval: int
    memory_stats_interval: int
    dump_detailed_report_at_memory_usage: int
    dump_removed_short_ids: bool
    dump_removed_short_ids_path: str
    enable_buffered_send: bool
    use_extensions: bool
    import_extensions: bool
    thread_pool_parallelism_degree: int
    tx_mem_pool_bucket_size: int
    source_version: str
    ca_cert_url: str
    private_ssl_base_url: str
    log_fluentd_queue_size: int
    log_level_fluentd: LogLevel
    log_level_stdout: LogLevel
    sync_tx_service: bool
    data_dir: str
    transaction_validation: bool

    rpc: bool
    rpc_port: int
    rpc_host: str
    rpc_user: str
    rpc_password: str
    rpc_use_ssl: bool
    rpc_ssl_base_url: str

    # set by node runner
    blockchain_networks: Dict[int, BlockchainNetworkModel]
    split_relays: bool
    blockchain_network_num: int
    outbound_peers: Set[OutboundPeerModel]
    node_type: NodeType
    logger_names: Optional[Iterable[str]]
    third_party_loggers: Optional[List[LoggerConfig]]
    using_private_ip_connection: bool

    # set after node runner
    has_fully_updated_tx_service: bool
    receive_buffer_size: int

    # hard coded configuration values
    stats_calculate_actual_size: bool
    log_detailed_block_stats: bool

    # set according to default values
    node_start_time: datetime
    os_version: str
    sid_expire_time: int
    block_compression_debug: bool
    enable_tcp_quickack: bool

    @classmethod
    def opts_defaults(cls, opts: Namespace) -> Namespace:
        opts.blockchain_networks = {}
        opts.split_relays = True
        opts.stats_calculate_actual_size = False
        opts.log_detailed_block_stats = False
        opts.blockchain_network_num = 0
        opts.outbound_peers = set()
        opts.node_type = NodeType.EXTERNAL_GATEWAY
        opts.has_fully_updated_tx_service = False
        opts.logger_names = []
        opts.third_party_loggers = None
        opts.node_start_time = datetime.utcnow()
        opts.os_version = constants.OS_VERSION
        opts.sid_expire_time = constants.SID_EXPIRE_TIME_SECONDS
        opts.enable_tcp_quickack = True
        opts.using_private_ip_connection = False
        opts.receive_buffer_size = constants.RECV_BUFSIZE

        return opts

    @classmethod
    def from_opts(cls, opts: Namespace):
        field_names = [field.name for field in dataclasses.fields(cls)]

        return cls(
            **{k: v for k, v in cls.opts_defaults(opts).__dict__.items() if k in field_names})

    def __post_init__(self) -> None:
        self.validate_external_ip()

    def validate_external_ip(self) -> None:
        parsed_sdn_url = parse.urlparse(self.sdn_url)
        sdn_host = parsed_sdn_url.netloc.split(":")[0]
        try:
            sdn_ip = ipaddress.ip_address(ip_resolver.blocking_resolve_ip(sdn_host))
            if not sdn_ip.is_private and self.external_ip and ipaddress.ip_address(self.external_ip).is_private:
                logger.fatal(
                    "The specified external IP ({}) is a known private IP address. Try omitting this argument",
                    self.external_ip,
                    exc_info=False
                )
                sys.exit(1)
        # pylint: disable=broad-except
        except Exception:
            logger.debug("SDN might be offline, skipping validate external ip")

    def validate_network_opts(self) -> None:
        pass

    def set_account_options(self, account_model: BdnAccountModelBase) -> None:
        pass
