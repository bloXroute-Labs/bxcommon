from dataclasses import dataclass
from typing import List
from bxcommon.models.serializeable_enum import SerializeableEnum

class NodeEventType(SerializeableEnum):
    PEER_CONN_ERR = "PEER_CONN_ERR"
    PEER_CONN_ESTABLISHED = "PEER_CONN_ESTABLISHED"
    PEER_CONN_CLOSED = "PEER_CONN_CLOSED"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    SID_SPACE_FULL = "SID_SPACE_FULL"
    BLOCKCHAIN_NODE_CONN_ERR = "BLOCKCHAIN_NODE_CONN_ERR"
    BLOCKCHAIN_NODE_CONN_ESTABLISHED = "BLOCKCHAIN_NODE_CONN_ESTABLISHED"
    REMOTE_BLOCKCHAIN_CONN_ERR = "REMOTE_BLOCKCHAIN_CONN_ERR"
    REMOTE_BLOCKCHAIN_CONN_ESTABLISHED = "REMOTE_BLOCKCHAIN_CONN_ESTABLISHED"
    TX_SERVICE_FULLY_SYNCED = "TX_SERVICE_FULLY_SYNCED"

@dataclass
class NodeEventModel:
    # What event happened in a node.
    node_id: str
    event_type: NodeEventType
    peer_ip: str = None
    peer_port: int = None
    timestamp: str = None
    event_id: str = None
