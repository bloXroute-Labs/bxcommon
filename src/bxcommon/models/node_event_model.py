class NodeEventModel(object):

    def __init__(self, node_id, event_type, peer_ip=None, peer_port=None, timestamp=None):
        self.node_id = node_id
        self.type = event_type
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.timestamp = timestamp


class NodeEventType(object):
    PEER_CONN_ERR = "PEER_CONN_ERR"
    PEER_CONN_ESTABLISHED = "PEER_CONN_ESTABLISHED"
    PEER_CONN_CLOSED = "PEER_CONN_CLOSED"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    SID_SPACE_FULL = "SID_SPACE_FULL"
    BLOCKCHAIN_NODE_CONN_ERR = "BLOCKCHAIN_NODE_CONN_ERR"
    BLOCKCHAIN_NODE_CONN_ESTABLISHED = "BLOCKCHAIN_NODE_CONN_ESTABLISHED"