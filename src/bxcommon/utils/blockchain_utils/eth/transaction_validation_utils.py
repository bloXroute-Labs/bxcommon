from typing import Optional, Union

import blxr_rlp as rlp

from bxcommon.utils.blockchain_utils.eth import crypto_utils
from bxcommon.utils.blockchain_utils.eth.eth_common_utils import keccak_hash
from bxcommon.messages.eth.serializers.transaction import Transaction
from bxcommon.models.tx_validation_status import TxValidationStatus


def verify_eth_transaction_signature(transaction: Transaction) -> bool:
    """
    checks eth transaction signature
    :param transaction:
    :return: if signature matches public key
    """
    try:
        signature = crypto_utils.encode_signature(transaction.v, transaction.r, transaction.s)
        unsigned_msg = transaction.get_unsigned()
        public_key = crypto_utils.recover_public_key(unsigned_msg, signature, keccak_hash)
        return crypto_utils.verify_signature(public_key, signature, keccak_hash(unsigned_msg))
    # pylint: disable=broad-except
    except Exception:
        return False


def parse_transaction(tx_bytes: memoryview) -> Optional[Transaction]:
    """
    :param tx_bytes: transaction bytes
    :return: if transaction successfully parsed returns None else transaction
    """

    try:
        payload = rlp.decode(bytearray(tx_bytes), strict=False)
        return Transaction.deserialize(payload)

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
    if isinstance(tx_bytes, bytearray):
        tx_bytes = memoryview(tx_bytes)

    transaction = parse_transaction(tx_bytes)
    if transaction:
        if verify_eth_transaction_signature(transaction):
            if transaction.gas_price >= min_tx_network_fee:
                return TxValidationStatus.VALID_TX
            else:
                return TxValidationStatus.LOW_FEE
        else:
            return TxValidationStatus.INVALID_SIGNATURE

    return TxValidationStatus.INVALID_FORMAT
