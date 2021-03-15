from dataclasses import dataclass

from bxcommon.models.serializeable_enum import SerializeableEnum


class NodeEventType(SerializeableEnum):
    PEER_CONN_ERR = "PEER_CONN_ERR"
    PEER_CONN_ESTABLISHED = "PEER_CONN_ESTABLISHED"
    PEER_CONN_CLOSED = "PEER_CONN_CLOSED"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    NOTIFY_OFFLINE = "NOTIFY_OFFLINE"
    SID_SPACE_EAGER_FETCH = "SID_SPACE_EAGER_FETCH"
    SID_SPACE_FULL = "SID_SPACE_FULL"
    SID_SPACE_SWITCH = "SID_SPACE_SWITCH"
    BLOCKCHAIN_NODE_CONN_ERR = "BLOCKCHAIN_NODE_CONN_ERR"
    BLOCKCHAIN_NODE_CONN_ESTABLISHED = "BLOCKCHAIN_NODE_CONN_ESTABLISHED"
    BLOCKCHAIN_NODE_CONN_ADDED = "BLOCKCHAIN_NODE_CONN_ADDED"
    BLOCKCHAIN_NODE_CONN_REMOVED = "BLOCKCHAIN_NODE_CONN_REMOVED"
    REMOTE_BLOCKCHAIN_CONN_ERR = "REMOTE_BLOCKCHAIN_CONN_ERR"
    REMOTE_BLOCKCHAIN_CONN_ESTABLISHED = "REMOTE_BLOCKCHAIN_CONN_ESTABLISHED"
    TX_SERVICE_FULLY_SYNCED = "TX_SERVICE_FULLY_SYNCED"
    TX_SERVICE_NOT_SYNCED = "TX_SERVICE_NOT_SYNCED"
    SWITCHING_RELAYS = "SWITCHING_RELAYS"

@dataclass
class NodeEventModel:
    # What event happened in a node.
    node_id: str
    # pyre-fixme[8]: Attribute has type `NodeEventType`; used as `None`.
    event_type: NodeEventType = None
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    peer_ip: str = None
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    peer_port: int = None
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    timestamp: str = None
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    event_id: str = None
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    payload: str = None

    # 'type' has been deprecated but remains here for backwards compatibility with versions pre 1.54.0.
    # TODO: Remove "type" attribute and "__post_init__" once all gateway versions in the BDN are > v1.54.0. Also, remove
    #  the default value of "None" for "event_type"
    # pyre-fixme[8]: Attribute has type `NodeEventType`; used as `None`.
    type: NodeEventType = None

    def __post_init__(self):
        if self.event_type is None:
            self.event_type = self.type
