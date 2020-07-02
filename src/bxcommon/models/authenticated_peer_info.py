from typing import NamedTuple, Optional
from bxcommon.connections.connection_type import ConnectionType
from bxutils import constants


class AuthenticatedPeerInfo(NamedTuple):
    connection_type: ConnectionType
    peer_id: str
    account_id: Optional[str]
    node_privileges: str = constants.DEFAULT_NODE_PRIVILEGES
