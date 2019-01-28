class BlockchainNetworkModel(object):

    def __init__(self, protocol=None, network=None, network_num=None, type=None, environment=None,
                 default_attributes=None):
        self.protocol = protocol
        self.network = network
        self.network_num = network_num
        self.type = type
        self.environment = environment
        self.default_attributes = default_attributes
