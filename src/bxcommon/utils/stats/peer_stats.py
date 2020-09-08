import dataclasses
import functools

from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, Optional


@dataclass
class PeerStatsMessage:
    bytes: int = 0
    count: int = 0


@dataclass
class PeerStats:
    address: str = ""
    peer_id: Optional[str] = None
    messages_received: Dict[str, PeerStatsMessage] = dataclasses.field(
        default_factory=functools.partial(defaultdict, PeerStatsMessage)
    )
    messages_sent: PeerStatsMessage = dataclasses.field(default_factory=PeerStatsMessage)
    peer_total_received: int = 0
    peer_total_sent: int = 0
    ping_max: float = 0
    ping_incoming_max: float = 0
    ping_outgoing_max: float = 0
