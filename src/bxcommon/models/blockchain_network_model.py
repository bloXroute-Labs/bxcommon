from dataclasses import dataclass
from bxcommon import constants
from typing import Dict, Any

@dataclass
class BlockchainNetworkModel(object):
    protocol: str
    network: str
    network_num: int
    type: str
    environment: str
    default_attributes: Dict[str, Any]
    block_interval: int
    ignore_block_interval_count: int
    final_tx_confirmations_count: int
    tx_contents_memory_limit_bytes: int
    max_tx_size_bytes: int

    def __init__(self, protocol: str = None, network: str = None, network_num: int = None, type: str = None,
                 environment: str = None, default_attributes: Dict[str, Any] = None, block_interval: int = None,
                 ignore_block_interval_count: int = None, final_tx_confirmations_count: int = None,
                 tx_contents_memory_limit_bytes: int = None, max_block_size_bytes: int = None,
                 max_tx_size_bytes: int = None):
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

    def __str__(self):
        return "({}, {}, {}, {}, {}, {}, {}, {}, {}, {})".\
            format(self.protocol, self.network, self.network_num, self.type, self.environment, self.default_attributes,
                   self.block_interval, self.ignore_block_interval_count, self.final_tx_confirmations_count, self.tx_contents_memory_limit_bytes)

    def __repr__(self):
        return "BlockchainNetworkModel" + self.__str__()

    def __eq__(self, other):
        return isinstance(other, BlockchainNetworkModel) and other.protocol == self.protocol and other.network == self.network \
               and other.network_num == self.network_num and other.type == self.type and other.environment == self.environment \
               and other.default_attributes == self.default_attributes and other.block_interval == self.block_interval \
               and other.ignore_block_interval_count == self.ignore_block_interval_count and other.final_tx_confirmations_count ==  self.final_tx_confirmations_count and other.tx_contents_memory_limit_bytes == self.tx_contents_memory_limit_bytes

    def __hash__(self):
        return hash(self.__repr__())
