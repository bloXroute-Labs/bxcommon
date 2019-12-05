from dataclasses import dataclass
from typing import Optional

from bxcommon import constants
from bxcommon.models.node_type import NodeType
from bxcommon.models.platform_provider import PlatformProvider


@dataclass(unsafe_hash=True)
class NodeModel:
    node_type: NodeType = None
    external_port: int = 0
    external_ip: str = None

    # Whether the node is online.
    online: bool = False

    # TODO: Remove this attribute as it's not being used anymore
    network: str = None

    # Internal id for distinguishing nodes.
    node_id: str = None

    # The starting and ending Transaction Short ID range, inclusive.
    sid_start: int = None
    sid_end: int = None

    sid_expire_time: int = None
    last_pong_time: int = 0
    is_gateway_miner: bool = False
    is_internal_gateway: bool = False

    # Current build's version
    source_version: str = None

    # Bloxroute protocol version
    protocol_version: int = None

    blockchain_network_num: int = None

    # IP address of the blockchain node
    blockchain_ip: str = None

    # Port of the blockchain node
    blockchain_port: int = None

    # Nodes hostname
    hostname: str = None

    sdn_id: str = None

    # Nodes OS version
    os_version: str = None

    continent: Optional[str] = None
    split_relays: bool = None
    country: str = None

    # idx enforces the one-way connection order of relays.
    # They connect to only other relays with an idx less than their own.
    idx: int = None

    has_fully_updated_tx_service: bool = False
    sync_txs_status = has_fully_updated_tx_service
    node_start_time: str = None

    # Ethereum remote blockchain attribute
    # Ethereum public key for remote blockchain connection
    node_public_key: str = None

    # number of redundant forwarding routes a particular relay expects by default
    baseline_route_redundancy: int = 0

    # number of redundant forwarding routes a particular relay expects to send to by default
    baseline_source_redundancy: int = 0

    private_ip: str = None
    csr: str = None
    cert: str = None

    platform_provider: PlatformProvider = None

    account_id: Optional[str] = None

    def __post_init__(self):
        self.sid_expire_time = constants.SID_EXPIRE_TIME_SECONDS
        # TODO: Remove network attribute, not being used
        if self.network is None:
            self.network = constants.DEFAULT_NETWORK_NAME
        if self.continent not in constants.DEFAULT_LIST_LOCATION_ORDER:
            self.continent = None
        if self.country:
            self.country = self.country[:constants.MAX_COUNTRY_LENGTH]
