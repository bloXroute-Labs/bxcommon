from dataclasses import dataclass
from typing import Any, Dict

from bxcommon import constants
from bxcommon.models.blockchain_network_environment import BlockchainNetworkEnvironment
from bxcommon.models.blockchain_network_type import BlockchainNetworkType


@dataclass
class BlockchainNetworkModel:
    protocol: str = None
    network: str = None
    network_num: int = constants.UNASSIGNED_NETWORK_NUMBER
    type: BlockchainNetworkType = None
    environment: BlockchainNetworkEnvironment = None
    default_attributes: Dict[str, Any] = None
    block_interval: int = None
    ignore_block_interval_count: int = None
    block_recovery_timeout_s: int = None
    block_hold_timeout_s: float = constants.DEFAULT_BLOCK_HOLD_TIMEOUT
    final_tx_confirmations_count: int = None
    tx_contents_memory_limit_bytes: int = None
    max_block_size_bytes: int = constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES
    max_tx_size_bytes: int = constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES
    block_confirmations_count: int = constants.BLOCK_CONFIRMATIONS_COUNT
    tx_percent_to_log_by_hash: float = constants.TRANSACTIONS_BY_HASH_PERCENTAGE_TO_LOG_STATS_FOR
    tx_percent_to_log_by_sid: float = constants.TRANSACTIONS_BY_SID_PERCENTAGE_TO_LOG_STATS_FOR
    removed_transactions_history_expiration_s: int = constants.REMOVED_TRANSACTIONS_HISTORY_EXPIRATION_S
    sdn_id: str = None
