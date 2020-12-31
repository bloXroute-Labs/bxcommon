from dataclasses import dataclass
from typing import Optional, Dict, Any

from bxcommon import constants
from bxcommon.models.node_type import NodeType


@dataclass
class OutboundPeerModel:
    ip: str
    port: int
    node_id: Optional[str]
    is_internal_gateway: bool
    node_type: Optional[NodeType]
    attributes: Dict[Any, Any]
    non_ssl_port: Optional[int]
    assigning_short_ids: bool
    idx: int

    def __init__(
        self,
        ip: str,
        port: int,
        node_id: Optional[str] = None,
        is_internal_gateway: bool = False,
        attributes: Optional[Dict[Any, Any]] = None,
        node_type: Optional[NodeType] = None,
        non_ssl_port: Optional[int] = None,
        assigning_short_ids: bool = False,
        idx: int = 0,
    ):
        if attributes is None:
            attributes = {}

        self.ip = ip
        self.port = port
        self.node_id = node_id
        self.is_internal_gateway = is_internal_gateway
        self.node_type = node_type
        self.attributes = attributes
        self.non_ssl_port = non_ssl_port
        self.assigning_short_ids = assigning_short_ids
        self.idx = idx

    def get_country(self) -> Optional[str]:
        if constants.NODE_COUNTRY_ATTRIBUTE_NAME in self.attributes:
            return self.attributes[constants.NODE_COUNTRY_ATTRIBUTE_NAME]

        return None

    def get_region(self) -> Optional[str]:
        if constants.NODE_REGION_ATTRIBUTE_NAME in self.attributes:
            return self.attributes[constants.NODE_REGION_ATTRIBUTE_NAME]

        return None

    def is_transaction_streamer(self) -> bool:
        return self.attributes.get(
            constants.TRANSACTION_STREAMER_ATTRIBUTE_NAME, False
        )

    def using_private_ip(self) -> bool:
        return self.attributes.get(
            constants.PRIVATE_IP_ATTRIBUTE_NAME, False
        )

    def __str__(self):
        return (
            f"({self.node_type}, {self.ip}, {self.port}, {self.node_id}, "
            f"{self.is_internal_gateway}, {self.non_ssl_port}, "
            f"{self.attributes}, assigning: {self.assigning_short_ids}, "
            f"idx: {self.idx})"
        )

    def __repr__(self):
        return "OutboundPeerModel" + self.__str__()

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, OutboundPeerModel)
            and other.node_id == self.node_id
            and other.port == self.port
            and other.ip == self.ip
        )

    def __hash__(self):
        return hash(f"{self.node_id}{self.ip}{self.port}")

    @classmethod
    def from_string(cls, peer_info_str: str) -> "OutboundPeerModel":
        try:
            peer_info = peer_info_str.split(":")
            ip = peer_info[0]
            port = peer_info[1]
            node_type = NodeType[peer_info[2].upper()] if len(peer_info) > 2 else NodeType.RELAY
            return OutboundPeerModel(ip, int(port), node_type=node_type)
        except Exception as _e:
            raise ValueError(f"{peer_info_str} is not a valid peer. Specify peer as ip:port:type string.")
