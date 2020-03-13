from typing import NamedTuple

from bxcommon.connections.connection_type import ConnectionType
from bxcommon.network.ip_endpoint import IpEndpoint
from bxcommon.network.transport_layer_protocol import TransportLayerProtocol


class ConnectionPeerInfo(NamedTuple):
    endpoint: IpEndpoint
    connection_type: ConnectionType
    transport_protocol: int = TransportLayerProtocol.TCP

    def __repr__(self) -> str:
        return f"{self.endpoint} [{self.connection_type.name}]"

    def __eq__(self, other: "ConnectionPeerInfo") -> bool:
        return self.endpoint == other.endpoint

    def __hash__(self):
        return hash(self.endpoint)
