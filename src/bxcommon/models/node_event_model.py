from dataclasses import dataclass


@dataclass()
class NodeEventModel(object):

    def __init__(self, node_id, event_type, peer_ip=None, peer_port=None, timestamp=None, tx_sync_networks=None):
        self.node_id = node_id
        self.type = event_type
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.timestamp = timestamp
        self.tx_sync_networks = tx_sync_networks


class NodeEventType(object):
    PEER_CONN_ERR = "PEER_CONN_ERR"
    PEER_CONN_ESTABLISHED = "PEER_CONN_ESTABLISHED"
    PEER_CONN_CLOSED = "PEER_CONN_CLOSED"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    NOTIFY_ONLINE = "NOTIFY_ONLINE"
    NOTIFY_OFFLINE = "NOTIFY_OFFLINE"
    SID_SPACE_FULL = "SID_SPACE_FULL"
    BLOCKCHAIN_NODE_CONN_ERR = "BLOCKCHAIN_NODE_CONN_ERR"
    BLOCKCHAIN_NODE_CONN_ESTABLISHED = "BLOCKCHAIN_NODE_CONN_ESTABLISHED"
    REMOTE_BLOCKCHAIN_CONN_ERR = "REMOTE_BLOCKCHAIN_CONN_ERR"
    REMOTE_BLOCKCHAIN_CONN_ESTABLISHED = "REMOTE_BLOCKCHAIN_CONN_ESTABLISHED"
    TX_SERVICE_FULLY_SYNCED = "TX_SERVICE_FULLY_SYNCED"
    TX_SERVICE_SYNCED_IN_NETWORK = "TX_SERVICE_SYNCED_IN_NETWORK"
