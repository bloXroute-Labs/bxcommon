class OutboundPeerModel(object):
    def __init__(self, ip, port, idx=None):
        self.ip = ip
        self.port = port
        self.idx = idx

    def __str__(self):
        return "({}, {}, {})".format(self.ip, self.port, self.idx)

    def __repr__(self):
        return "OutboundPeerModel" + self.__str__()

    def __eq__(self, other):
        return isinstance(other, OutboundPeerModel) and other.ip == self.ip and other.port == self.port \
               and other.idx == self.idx


