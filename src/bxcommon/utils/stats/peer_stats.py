from collections import defaultdict
from typing import Dict, Optional


class PeerStatsMessage:
    bytes: int
    count: int

    def __init__(self) -> None:
        self.bytes = 0
        self.count = 0


class PeerStats:
    address: str
    peer_id: Optional[str]
    messages_received: Dict[str, PeerStatsMessage]
    messages_sent: PeerStatsMessage
    peer_total_received: int
    peer_total_sent: int
    ping_max: float

    def __init__(self) -> None:
        self.address = ""
        self.peer_id = None
        self.messages_received = defaultdict(PeerStatsMessage)
        self.messages_sent = PeerStatsMessage()
        self.peer_total_received = 0
        self.peer_total_sent = 0
        self.ping_max = 0
