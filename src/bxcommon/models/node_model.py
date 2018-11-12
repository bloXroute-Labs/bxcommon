class NodeModel(object):
    def __init__(self, node_type=None, external_ip=None, external_port=None, network=None, online=None, node_id=None,
                 sid_start=None, sid_end=None, idx=None, sid_expire_time=None, last_pong_time=None):
        self.external_port = external_port
        self.network = network
        self.online = online
        self.node_id = node_id
        self.sid_start = sid_start
        self.sid_end = sid_end
        self.idx = idx
        self.sid_expire_time = sid_expire_time
        self.node_type = node_type
        self.external_ip = external_ip
        self.last_pong_time = last_pong_time
