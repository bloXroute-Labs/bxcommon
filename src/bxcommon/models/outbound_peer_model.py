from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from bxcommon import constants
from bxcommon.models.node_type import NodeType


@dataclass
class OutboundPeerModel:
    ip: str
    port: int
    node_id: Optional[str]
    is_internal_gateway: bool
    node_type:  Optional[NodeType]
    attributes: Dict[Any, Any]
    non_ssl_port: Optional[int]

    def __init__(self, ip: str = None, port: int = None, node_id: Optional[str] = None,
                 is_internal_gateway: bool = False, attributes: Dict[Any, Any] = None,
                 node_type: Optional[NodeType] = None):
        if attributes is None:
            attributes = {}

        self.ip = ip
        self.port = port
        self.node_id = node_id
        self.is_internal_gateway = is_internal_gateway
        self.node_type = node_type
        self.attributes = attributes

    def get_country(self):
        if constants.NODE_COUNTRY_ATTRIBUTE_NAME in self.attributes:
            return self.attributes[constants.NODE_COUNTRY_ATTRIBUTE_NAME]

        return None

    def __str__(self):
        return "({}, {}, {}, {}, {}, {})".format(self.node_type, self.ip, self.port, self.node_id,
                                                 self.is_internal_gateway, self.attributes)

    def __repr__(self):
        return "OutboundPeerModel" + self.__str__()

    def __eq__(self, other) -> bool:
        return isinstance(other, OutboundPeerModel) and other.node_id == self.node_id and other.port == self.port and\
               other.ip == self.ip

    def __hash__(self):
        return hash("{}{}{}".format(self.node_id, self.ip, self.port))
