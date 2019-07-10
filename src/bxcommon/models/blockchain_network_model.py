from dataclasses import dataclass
from bxcommon import constants


@dataclass
class BlockchainNetworkModel(object):

    def __init__(self, protocol=None, network=None, network_num=None, type=None, environment=None,
                 default_attributes=None, block_interval=None, ignore_block_interval_count=None,
                 final_tx_confirmations_count=None, tx_contents_memory_limit_bytes=None, max_block_size_bytes=None,
                 max_tx_size_bytes=None):
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

        if max_block_size_bytes is None:
            self.max_block_size_bytes = constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES
        else:
            self.max_block_size_bytes = max_block_size_bytes

        if max_tx_size_bytes is None:
            self.max_tx_size_bytes = constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES
        else:
            self.max_tx_size_bytes = max_tx_size_bytes
