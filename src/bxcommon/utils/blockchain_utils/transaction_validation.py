from typing import Union, Dict, Callable

from bxcommon.utils.blockchain_utils.eth import transaction_validation_utils
from bxcommon.models.blockchain_protocol import BlockchainProtocol
from bxcommon.models.tx_validation_status import TxValidationStatus

protocol_transaction_validation: Dict[BlockchainProtocol, Callable[
    [Union[bytes, bytearray, memoryview], int],
    TxValidationStatus
]]
network_num_to_protocol: Dict[int, str]


def validate_transaction(
    tx_bytes: Union[bytes, bytearray, memoryview],
    protocol: BlockchainProtocol,
    min_tx_network_fee: int
) -> TxValidationStatus:
    return protocol_transaction_validation[protocol](tx_bytes, min_tx_network_fee)


def btc_validate_transaction(
    _tx_bytes: Union[bytes, bytearray, memoryview],
    _min_tx_network_fee: int
) -> TxValidationStatus:
    return TxValidationStatus.VALID_TX


def eth_validate_transaction(
    tx_bytes: Union[bytes, bytearray, memoryview],
    min_tx_network_fee: int
) -> TxValidationStatus:
    if isinstance(tx_bytes, bytes):
        tx_bytes = bytearray(tx_bytes)
    return transaction_validation_utils.validate_transaction(tx_bytes, min_tx_network_fee)


def ont_validate_transaction(
    _tx_bytes: Union[bytes, bytearray, memoryview],
    _min_tx_network_fee: int
) -> TxValidationStatus:
    return TxValidationStatus.VALID_TX


protocol_transaction_validation = {
    BlockchainProtocol.BITCOIN: btc_validate_transaction,
    BlockchainProtocol.BITCOINCASH: btc_validate_transaction,
    BlockchainProtocol.ETHEREUM: eth_validate_transaction,
    BlockchainProtocol.ONTOLOGY: ont_validate_transaction

}
