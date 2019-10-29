from collections import defaultdict


class PeerStats:
    def __init__(self):
        self.address = ""
        self.peer_id = None
        self.messages_received = defaultdict(PeerStatsMessage)
        self.messages_sent = PeerStatsMessage()
        self.peer_total_received = 0
        self.peer_total_sent = 0
        self.ping_max = 0


class PeerStatsMessage:
    def __init__(self):
        self.bytes = 0
        self.count = 0
