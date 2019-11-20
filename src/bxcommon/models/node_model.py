from bxcommon import constants
from dataclasses import dataclass
from typing import Optional
from bxcommon.connections.node_type import NodeType

@dataclass
class NodeModel:
    external_port: int = None

    # Whether the node is online.
    online: bool = None

    external_ip: str = None

    # The network of the node, e.g. main, test, local.
    network: str = None

    # Internal id for distinguishing nodes.
    node_id: str = None

    # The starting and ending Transaction Short ID range, inclusive.
    sid_start: int = None
    sid_end: int = None

    sid_expire_time: int = None
    node_type: NodeType = None
    last_pong_time: int = None
    is_gateway_miner: bool = None
    is_internal_gateway: bool = None

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

    def __post_init__(self):
        # TODO: Remove network attribute, not being used
        if self.network == None:
            self.network = constants.DEFAULT_NETWORK_NAME
        if self.continent not in constants.DEFAULT_LIST_LOCATION_ORDER:
            self.continent = None
        if self.country:
            self.country = self.country[:constants.MAX_COUNTRY_LENGTH]

