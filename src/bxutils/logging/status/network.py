
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bxcommon.connections.connection_type import ConnectionType
from bxutils.logging.status.blockchain_connection import BlockchainConnection
from bxutils.logging.status.connection_state import ConnectionState
from bxutils.logging.status.gateway_status import GatewayStatus
from bxutils.logging.status.relay_connection import RelayConnection
from bxutils.logging.status.summary import Summary


@dataclass
class Network:
    block_relay: RelayConnection
    transaction_relay: RelayConnection
    blockchain_node: BlockchainConnection
    remote_blockchain_node: BlockchainConnection

    def get_summary(self) -> Summary:
        block_relay_connection_state = self.block_relay.get_connection_state()
        transaction_relay_connection_state = self.transaction_relay.get_connection_state()
        blockchain_node_connection_state = self.blockchain_node.get_connection_state()
        remote_blockchain_node_connection_state = self.remote_blockchain_node.get_connection_state()
        if block_relay_connection_state == transaction_relay_connection_state == blockchain_node_connection_state == \
                remote_blockchain_node_connection_state == ConnectionState.ESTABLISHED:
            gateway_status = GatewayStatus.ONLINE
        else:
            gateway_status = GatewayStatus.WITH_ERRORS
        return Summary(gateway_status, block_relay_connection_state, transaction_relay_connection_state,
                       blockchain_node_connection_state, remote_blockchain_node_connection_state)

    def update_connection(self, conn: ConnectionType, desc: Optional[str] = None, fileno: Optional[str] = None,
                          peer_id: Optional[str] = None) -> None:
        ip_addr = None if desc is None else desc.split()[0]
        port = None if desc is None else desc.split()[1]
        current_time = _get_current_time()

        if conn == ConnectionType.RELAY_BLOCK:
            self.block_relay = RelayConnection(ip_addr, port, fileno, peer_id, current_time)
        elif conn == ConnectionType.RELAY_TRANSACTION:
            self.transaction_relay = RelayConnection(ip_addr, port, fileno, peer_id, current_time)
        elif conn == ConnectionType.BLOCKCHAIN_NODE:
            self.blockchain_node = BlockchainConnection(ip_addr, port, fileno, current_time)
        else:
            self.remote_blockchain_node = BlockchainConnection(ip_addr, port, fileno, current_time)


def _get_current_time() -> str:
    return "UTC " + str(datetime.utcnow())