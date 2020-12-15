from dataclasses import dataclass
from typing import Optional

from bxcommon import constants
from bxcommon.models.node_type import NodeType
from bxcommon.models.platform_provider import PlatformProvider
from bxutils import constants as util_constants


@dataclass
class NodeModel:
    # pyre-fixme[8]: Attribute has type `NodeType`; used as `None`.
    node_type: NodeType = None
    external_port: int = 0
    non_ssl_port: int = 0
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    external_ip: str = None

    # Whether the node is online.
    online: Optional[bool] = False

    # Whether node has active connection with SDN
    sdn_connection_alive: bool = False

    # TODO: Remove this attribute as it's not being used anymore
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    network: str = None

    # Internal id for distinguishing nodes.
    node_id: Optional[str] = None

    # The starting and ending Transaction Short ID range, inclusive.
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    sid_start: int = None
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    sid_end: int = None
    next_sid_start: Optional[int] = None
    next_sid_end: Optional[int] = None

    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    sid_expire_time: int = None
    last_pong_time: float = 0
    is_gateway_miner: bool = False
    is_internal_gateway: bool = False

    # Current build's version
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    source_version: str = None

    # Bloxroute protocol version
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    protocol_version: int = None

    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    blockchain_network_num: int = None

    # IP address of the blockchain node
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    blockchain_ip: str = None

    # Port of the blockchain node
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    blockchain_port: int = None

    # Nodes hostname
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    hostname: str = None

    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    sdn_id: str = None

    # Nodes OS version
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    os_version: str = None

    continent: Optional[str] = None
    # pyre-fixme[8]: Attribute has type `bool`; used as `None`.
    split_relays: bool = None
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    country: str = None
    region: Optional[str] = None

    # idx enforces the one-way connection order of relays.
    # They connect to only other relays with an idx less than their own.
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    idx: int = None

    has_fully_updated_tx_service: bool = False
    sync_txs_status = has_fully_updated_tx_service
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    node_start_time: str = None

    # Ethereum remote blockchain attribute
    # Ethereum public key for remote blockchain connection
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    node_public_key: str = None

    # number of redundant forwarding routes a particular relay expects by default
    baseline_route_redundancy: int = 0

    # number of redundant forwarding routes a particular relay expects to send to by default
    baseline_source_redundancy: int = 0

    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    private_ip: str = None
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    csr: str = None
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    cert: str = None
    # pyre-fixme[8]: Attribute has type `PlatformProvider`; used as `None`.
    platform_provider: PlatformProvider = None

    account_id: Optional[str] = None

    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    latest_source_version: str = None
    should_update_source_version: bool = False

    assigning_short_ids: Optional[bool] = False

    # blockchain node privileges for segmenting gateway types within a blockchain network
    # this property is ignored for relays
    node_privileges: str = util_constants.DEFAULT_NODE_PRIVILEGES

    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    first_seen_time: str = None

    is_docker: bool = False
    using_private_ip_connection: bool = False

    private_node: bool = False

    def __post_init__(self):
        self.sid_expire_time = constants.SID_EXPIRE_TIME_SECONDS
        # TODO: Remove network attribute, not being used
        if self.network is None:
            self.network = constants.DEFAULT_NETWORK_NAME
        if self.continent not in constants.DEFAULT_LIST_LOCATION_ORDER:
            self.continent = None
        if self.country:
            self.country = self.country[:constants.MAX_COUNTRY_LENGTH]

    def __eq__(self, other) -> bool:
        return isinstance(other, NodeModel) and other.node_id == self.node_id

    def __hash__(self):
        return hash(self.node_id)
