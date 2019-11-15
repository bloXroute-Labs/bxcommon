from dataclasses import dataclass
from typing import Dict, Any

from bxcommon import constants
from bxcommon.models.blockchain_network_environment import BlockchainNetworkEnvironment
from bxcommon.models.blockchain_network_type import BlockchainNetworkType


@dataclass
class BlockchainNetworkModel:
    protocol: str
    network: str
    network_num: int
    type: BlockchainNetworkType
    environment: BlockchainNetworkEnvironment
    default_attributes: Dict[str, Any]
    block_interval: int
    ignore_block_interval_count: int
    block_recovery_timeout_s: int
    block_hold_timeout_s: float
    final_tx_confirmations_count: int
    tx_contents_memory_limit_bytes: int
    max_block_size_bytes: int = constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES
    max_tx_size_bytes: int = constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES
    block_confirmations_count: int = constants.BLOCK_CONFIRMATIONS_COUNT
    tx_percent_to_log: float = constants.TRANSACTIONS_PERCENTAGE_TO_LOG_STATS_FOR
