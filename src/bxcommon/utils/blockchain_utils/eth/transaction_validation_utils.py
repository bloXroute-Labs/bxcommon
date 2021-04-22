from typing import Optional, Union

from bxcommon.utils.blockchain_utils.eth import crypto_utils, rlp_utils
from bxcommon.utils.blockchain_utils.eth.eth_common_utils import keccak_hash
from bxcommon.messages.eth.serializers.transaction import Transaction
from bxcommon.models.tx_validation_status import TxValidationStatus

import blxr_rlp as rlp


def verify_eth_transaction_signature(transaction: Transaction) -> bool:
    """
    checks eth transaction signature
    :param transaction:
    :return: if signature matches public key
    """
    try:
        signature = transaction.signature()
        unsigned_msg = transaction.get_unsigned()
        public_key = crypto_utils.recover_public_key(unsigned_msg, signature, keccak_hash)
        return crypto_utils.verify_signature(public_key, signature, keccak_hash(memoryview(unsigned_msg)))
    # pylint: disable=broad-except
    except Exception:
        return False


def normalize_typed_transaction(tx_bytes: memoryview) -> memoryview:
    """
    RLP could be either [transaction_type][encoded transaction], or
    RLP([transaction_type][encoded transaction]). The first form cannot be
    `rlp.decode`d, as it will only return the transaction type or throw an
    exception if strict=True. Force it to be of the second type.
    """
    item_type, item_length, item_start = rlp_utils.consume_length_prefix(tx_bytes, 0)
    if item_type == str and item_length == 1:
        tx_bytes = memoryview(rlp.encode(tx_bytes.tobytes()))

    return tx_bytes


def parse_transaction(tx_bytes: memoryview) -> Optional[Transaction]:
    """
    :param tx_bytes: transaction bytes
    :return: if transaction successfully parsed returns None else transaction
    """
    try:
        tx_bytes = normalize_typed_transaction(tx_bytes)
        return rlp.decode(tx_bytes.tobytes(), Transaction)
    # pylint: disable=broad-except
    except Exception:
        return None


def validate_transaction(
    tx_bytes: Union[bytearray, memoryview],
    min_tx_network_fee: int
) -> TxValidationStatus:
    """
    check if transaction is validated - signature is correct and format is valid
    :param tx_bytes:
    :param min_tx_network_fee: int
    :return:
    """
    tx_bytes = normalize_typed_transaction(memoryview(tx_bytes))

    if isinstance(tx_bytes, memoryview):
        tx_bytes = bytearray(tx_bytes)

    try:
        transaction = rlp.decode(tx_bytes, Transaction)
        if verify_eth_transaction_signature(transaction):
            if transaction.gas_price >= min_tx_network_fee:
                return TxValidationStatus.VALID_TX
            else:
                return TxValidationStatus.LOW_FEE
        else:
            return TxValidationStatus.INVALID_SIGNATURE
    except rlp.DecodingError:
        return TxValidationStatus.INVALID_FORMAT
