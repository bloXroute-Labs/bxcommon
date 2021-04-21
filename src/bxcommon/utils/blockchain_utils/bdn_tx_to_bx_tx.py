from typing import Union, Optional, Dict, Callable

from bxcommon.exceptions import ParseError
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.models.blockchain_protocol import BlockchainProtocol
from bxcommon.models.transaction_flag import TransactionFlag
from bxcommon.utils.blockchain_utils.btc import btc_common_utils
from bxcommon.utils.blockchain_utils.eth import eth_common_utils
from bxcommon.utils.blockchain_utils.ont import ont_common_utils
from bxcommon import constants

protocol_to_bdn_tx_to_bx_tx: Dict[BlockchainProtocol, Callable[
    [Union[bytes, bytearray, memoryview], int, Optional[TransactionFlag], str],
    TxMessage
]]
network_num_to_protocol: Dict[int, str]


def init(blockchain_networks: Dict[int, BlockchainNetworkModel]):
    # pylint: disable=global-statement
    global network_num_to_protocol
    network_num_to_protocol = {}
    for network_num, blockchain_network in blockchain_networks.items():
        network_num_to_protocol[network_num] = blockchain_network.protocol.lower()


def bdn_tx_to_bx_tx(
    raw_tx: Union[bytes, bytearray, memoryview],
    network_num: int,
    transaction_flag: Optional[TransactionFlag] = None,
    account_id: str = constants.DECODED_EMPTY_ACCOUNT_ID
) -> TxMessage:
    try:
        current_protocol = network_num_to_protocol[network_num]
    except KeyError:
        raise ValueError(f"{network_num} does not exist.")
    blockchain_protocol = BlockchainProtocol(current_protocol)
    return protocol_to_bdn_tx_to_bx_tx[blockchain_protocol](raw_tx, network_num, transaction_flag, account_id)


def btc_bdn_tx_to_bx_tx(
    raw_tx: Union[bytes, bytearray, memoryview],
    network_num: int,
    transaction_flag: Optional[TransactionFlag] = None,
    account_id: str = constants.DECODED_EMPTY_ACCOUNT_ID
) -> TxMessage:
    if isinstance(raw_tx, bytes):
        raw_tx = bytearray(raw_tx)
    try:
        tx_hash = btc_common_utils.get_txid(raw_tx)
    except IndexError:
        raise ValueError("Invalid raw transaction provided.")
    return TxMessage(
        message_hash=tx_hash,
        network_num=network_num,
        tx_val=raw_tx,
        transaction_flag=transaction_flag,
        account_id=account_id
    )


def eth_bdn_tx_to_bx_tx(
    raw_tx: Union[bytes, bytearray, memoryview],
    network_num: int,
    transaction_flag: Optional[TransactionFlag] = None,
    account_id: str = constants.DECODED_EMPTY_ACCOUNT_ID
) -> TxMessage:
    if isinstance(raw_tx, bytes):
        raw_tx = bytearray(raw_tx)
    bx_tx, _, tx_item_length, tx_item_start = eth_common_utils.raw_tx_to_bx_tx(
        raw_tx, 0, network_num, transaction_flag, account_id
    )
    if tx_item_length + tx_item_start != len(raw_tx):
        raise ParseError(raw_tx)
    return bx_tx


def ont_bdn_tx_to_bx_tx(
    raw_tx: Union[bytes, bytearray, memoryview],
    network_num: int,
    transaction_flag: Optional[TransactionFlag] = None,
    account_id: str = constants.DECODED_EMPTY_ACCOUNT_ID
) -> TxMessage:
    if isinstance(raw_tx, bytes):
        raw_tx = bytearray(raw_tx)
    try:
        tx_hash, _ = ont_common_utils.get_txid(raw_tx)
    except IndexError:
        raise ValueError("Invalid raw transaction provided.")
    return TxMessage(
        message_hash=tx_hash,
        network_num=network_num,
        tx_val=raw_tx,
        transaction_flag=transaction_flag,
        account_id=account_id
    )


protocol_to_bdn_tx_to_bx_tx = {
    BlockchainProtocol.BITCOIN: btc_bdn_tx_to_bx_tx,
    BlockchainProtocol.BITCOINCASH: btc_bdn_tx_to_bx_tx,
    BlockchainProtocol.ETHEREUM: eth_bdn_tx_to_bx_tx,
    BlockchainProtocol.ONTOLOGY: ont_bdn_tx_to_bx_tx

}
