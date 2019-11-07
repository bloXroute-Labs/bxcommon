from collections import defaultdict


class PeerStats(object):
    def __init__(self):
        self.address = ""
        self.messages_received = defaultdict(PeerStatsMessage)
        self.messages_sent = PeerStatsMessage()
        self.peer_total_received = 0
        self.peer_total_sent = 0
        self.ping_max = 0


class PeerStatsMessage(object):
    def __init__(self):
        self.bytes = 0
        self.count = 0
