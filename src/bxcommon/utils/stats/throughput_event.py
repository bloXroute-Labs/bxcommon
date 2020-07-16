class ThroughputEvent:
    def __init__(self, direction, msg_type, msg_size, peer_desc) -> None:
        self.direction = direction
        self.msg_type = msg_type
        self.msg_size = msg_size
        self.peer_desc = peer_desc
