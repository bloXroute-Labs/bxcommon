class ThroughputEvent(object):
    def __init__(self, direction, msg_type, num_bytes, peer_desc):
        self.direction = direction
        self.msg_type = msg_type
        self.num_bytes = num_bytes
        self.peer_desc = peer_desc
