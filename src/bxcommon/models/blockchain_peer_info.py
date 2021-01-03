from dataclasses import dataclass
from typing import Optional

from bxcommon.utils.blockchain_utils.eth import eth_common_constants


@dataclass
class BlockchainPeerInfo:
    ip: str
    port: int
    node_public_key: Optional[str] = None
    blockchain_protocol_version: int = eth_common_constants.ETH_PROTOCOL_VERSION
    connection_established: bool = False

    def __repr__(self):
        return f"BlockchainPeerInfo(ip address: {self.ip}, " \
               f"port: {self.port}, " \
               f"node public key: {self.node_public_key}, " \
               f"blockchain protocol version: {self.blockchain_protocol_version})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, BlockchainPeerInfo)
            and other.port == self.port
            and other.ip == self.ip
        )

    def __hash__(self):
        return hash(f"{self.ip}:{self.port}")
