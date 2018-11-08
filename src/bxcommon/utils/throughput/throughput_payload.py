class ThroughputPayload(object):

    def __init__(self, start_time, current_time, node_type=None, node_address=None, total_bytes_received=0,
                 total_bytes_sent=0):
        self.node_type = node_type
        self.node_address = node_address
        self.node_peers = []
        self.total_bytes_received = total_bytes_received
        self.total_bytes_sent = total_bytes_sent
        self.peer_stats = []
        self.start_time = str(start_time)
        self.current_time = str(current_time)
