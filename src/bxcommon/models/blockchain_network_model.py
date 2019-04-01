class BlockchainNetworkModel(object):

    def __init__(self, protocol=None, network=None, network_num=None, type=None, environment=None,
                 default_attributes=None, block_interval=None, ignore_block_interval_count=None,
                 final_tx_confirmations_count=None, tx_contents_memory_limit_bytes=None):
        self.protocol = protocol
        self.network = network
        self.network_num = network_num
        self.type = type
        self.environment = environment
        self.default_attributes = default_attributes
        self.block_interval = block_interval
        self.ignore_block_interval_count = ignore_block_interval_count
        self.final_tx_confirmations_count = final_tx_confirmations_count
        self.tx_contents_memory_limit_bytes = tx_contents_memory_limit_bytes
