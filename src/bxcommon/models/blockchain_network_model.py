from dataclasses import dataclass
from typing import Any, Dict

from bxcommon import constants
from bxcommon.models.blockchain_network_environment import BlockchainNetworkEnvironment
from bxcommon.models.blockchain_network_type import BlockchainNetworkType


@dataclass
class BlockchainNetworkModel:
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    protocol: str = None
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    network: str = None
    network_num: int = constants.UNASSIGNED_NETWORK_NUMBER
    # pyre-fixme[8]: Attribute has type `BlockchainNetworkType`; used as `None`.
    type: BlockchainNetworkType = None
    # pyre-fixme[8]: Attribute has type `BlockchainNetworkEnvironment`; used as `None`.
    environment: BlockchainNetworkEnvironment = None
    # pyre-fixme[8]: Attribute has type `Dict[str, typing.Any]`; used as `None`.
    default_attributes: Dict[str, Any] = None
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    block_interval: int = None
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    ignore_block_interval_count: int = None
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    block_recovery_timeout_s: int = None
    block_hold_timeout_s: float = constants.DEFAULT_BLOCK_HOLD_TIMEOUT
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    final_tx_confirmations_count: int = None
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    tx_contents_memory_limit_bytes: int = None
    max_block_size_bytes: int = constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES
    max_tx_size_bytes: int = constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES
    block_confirmations_count: int = constants.BLOCK_CONFIRMATIONS_COUNT
    tx_percent_to_log_by_hash: float = constants.TRANSACTIONS_BY_HASH_PERCENTAGE_TO_LOG_STATS_FOR
    tx_percent_to_log_by_sid: float = constants.TRANSACTIONS_BY_SID_PERCENTAGE_TO_LOG_STATS_FOR
    removed_transactions_history_expiration_s: int = constants.REMOVED_TRANSACTIONS_HISTORY_EXPIRATION_S
    # pyre-fixme[8]: Attribute has type `str`; used as `None`.
    sdn_id: str = None
    tx_sync_interval_s: float = constants.GATEWAY_SYNC_TX_THRESHOLD_S
    tx_sync_sync_content: bool = constants.GATEWAY_SYNC_SYNC_CONTENT
    enable_network_content_logs: bool = False
    enable_block_compression: bool = True
    # Denoted in GWEI for Ethereum
    min_tx_network_fee: int = 0
    medium_tx_network_fee: int = 0
    min_tx_age_seconds: float = 0.0

    mempool_expected_transactions_count: int = 0
    send_compressed_txs_after_block: bool = False
    log_compressed_block_debug_info_on_relay: bool = True

    enable_recording_tx_detection_time_location: bool = True
    enable_check_sender_nonce: bool = True
    allowed_time_reuse_sender_nonce: float = 0.0
    allowed_gas_price_change_reuse_sender_nonce: float = 1.1
