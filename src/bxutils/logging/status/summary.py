from dataclasses import dataclass
from typing import Optional

from bxutils.logging.status.connection_state import ConnectionState
from bxutils.logging.status.gateway_status import GatewayStatus


@dataclass
class Summary:
    gateway_status: Optional[GatewayStatus] = None
    block_relay_connection_state: Optional[ConnectionState] = None
    transaction_relay_connection_state: Optional[ConnectionState] = None
    blockchain_node_connection_state: Optional[ConnectionState] = None
    remote_blockchain_node_connection_state: Optional[ConnectionState] = None
