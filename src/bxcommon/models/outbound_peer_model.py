from dataclasses import dataclass


@dataclass
class OutboundPeerModel(object):
    def __init__(self, ip=None, port=None, node_id=None, is_internal_gateway=False, attributes=None):
        if attributes is None:
            attributes = {}

        self.ip = ip
        self.port = port
        self.node_id = node_id
        self.is_internal_gateway = is_internal_gateway
        self.attributes = attributes

    def __str__(self):
        return "({}, {}, {}, {}, {})".format(self.ip, self.port, self.node_id, self.is_internal_gateway,
                                             self.attributes)

    def __repr__(self):
        return "OutboundPeerModel" + self.__str__()

    def __eq__(self, other):
        return isinstance(other, OutboundPeerModel) and other.ip == self.ip and other.port == self.port \
               and other.node_id == self.node_id and other.is_internal_gateway == self.is_internal_gateway

    def __hash__(self):
        return hash(self.__repr__())
