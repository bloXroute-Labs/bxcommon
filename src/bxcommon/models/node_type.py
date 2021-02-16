import enum
from typing import Iterable

from bxcommon.models.serializable_flag import SerializableFlag


class NodeType(SerializableFlag):
    INTERNAL_GATEWAY = enum.auto()
    EXTERNAL_GATEWAY = enum.auto()
    # deprecated, use GATEWAY_TYPE for abstract gateway,
    # GATEWAY for v1.0 gateways
    GATEWAY = INTERNAL_GATEWAY | EXTERNAL_GATEWAY
    GATEWAY_TYPE = GATEWAY
    RELAY_TRANSACTION = enum.auto()
    RELAY_BLOCK = enum.auto()
    RELAY = RELAY_TRANSACTION | RELAY_BLOCK
    RELAY_TYPE = RELAY  # use RELAY_TYPE for abstract relay, use RELAY for `non split` relay
    RELAY_PROXY = enum.auto()
    RELAY_GROUP = RELAY | RELAY_PROXY
    API = enum.auto()
    API_SOCKET = enum.auto()
    BLOXROUTE_CLOUD_API = enum.auto()
    JOBS = enum.auto()

    def get_subtypes(self) -> Iterable["NodeType"]:
        for subtype in self.__class__:
            if subtype in self:
                yield subtype
