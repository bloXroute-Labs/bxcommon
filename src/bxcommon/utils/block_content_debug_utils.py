from typing import Union, Optional, List, Tuple

from bxcommon.messages.bloxroute import compact_block_short_ids_serializer
from bxcommon.models.node_type import NodeType
from bxcommon.models.transaction_info import TransactionInfo
from bxcommon.services.transaction_service import TransactionService
from bxcommon.utils.blockchain_utils.eth import rlp_utils, eth_common_utils
from bxcommon.utils.object_hash import Sha256Hash
from bxutils import logging
from bxutils.logging import LogLevel

logger = logging.get_logger(__name__)


def log_compressed_block_debug_info(transaction_service: TransactionService,
                                    block_msg_bytes: Union[memoryview, bytearray]):
    if logger.isEnabledFor(LogLevel.TRACE) and transaction_service.node.opts.block_compression_debug:
        network_num = transaction_service.network_num
        protocol = transaction_service.node.opts.blockchain_networks[network_num].protocol

        # TODO implement in a better way
        if protocol.lower() == "ethereum":
            _log_compressed_block_debug_info_eth(transaction_service, block_msg_bytes)


def log_can_decompress_block(node_type: NodeType,
                             block_hash: Sha256Hash,
                             missing_short_ids: Optional[List[Union[int, TransactionInfo]]]):
    if node_type != NodeType.RELAY_BLOCK:
        if missing_short_ids:
            logger.debug("Can decompress block {}: NO", block_hash)
            logger.debug(
                "Block {} has missing compressed transactions: {}",
                block_hash,
                missing_short_ids
            )
        else:
            logger.debug("Can decompress block {}: YES", block_hash)


def _log_compressed_block_debug_info_eth(transaction_service: TransactionService,
                                         block_msg_bytes: Union[memoryview, bytearray]):
    is_block_relay = transaction_service.node.NODE_TYPE == NodeType.RELAY_BLOCK
    block_hash, short_ids, txs_bytes = _parse_block_eth(block_msg_bytes)

    # parse statistics variables
    short_tx_index = 0
    tx_start_index = 0

    tx_index_in_block = 0
    txs_info = []
    missing_short_ids = []

    while True:
        if tx_start_index >= len(txs_bytes):
            break

        short_id = 0
        has_contents = False
        assignmnet_time = 0

        _, tx_itm_len, tx_itm_start = rlp_utils.consume_length_prefix(txs_bytes, tx_start_index)
        tx_bytes = txs_bytes[tx_itm_start:tx_itm_start + tx_itm_len]

        is_full_tx_start = 0
        is_full_tx, is_full_tx_len, = rlp_utils.decode_int(tx_bytes, is_full_tx_start)

        _, tx_content_len, tx_content_start = rlp_utils.consume_length_prefix(
            tx_bytes, is_full_tx_start + is_full_tx_len)
        tx_content_bytes = tx_bytes[tx_content_start:tx_content_start + tx_content_len]

        if is_full_tx:
            tx_hash = Sha256Hash(eth_common_utils.keccak_hash(tx_content_bytes))
        else:
            short_id = short_ids[short_tx_index]
            tx_hash, tx_bytes, _ = transaction_service.get_transaction(short_id)
            has_contents = tx_bytes is not None
            if tx_hash is not None:
                assignmnet_time = transaction_service.get_short_id_assign_time(short_id)
            short_tx_index += 1

        if is_block_relay:
            txs_info.append((tx_index_in_block, not is_full_tx, short_id, tx_hash))
        else:
            txs_info.append((tx_index_in_block, not is_full_tx, short_id, tx_hash, has_contents, assignmnet_time))

        tx_index_in_block += 1
        tx_start_index = tx_itm_start + tx_itm_len

        if not is_full_tx and not has_contents:
            missing_short_ids.append(short_id)

    if is_block_relay:
        log_message = \
            "Block content (from block relay) {} from (index, is compressed, short id, hash is full) : {}"
    else:
        log_message = \
            "Block content (full) {} (index, compressed, short id, hash, has contents, assignment time) : {}"

    logger.debug(
        log_message,
        block_hash,
        ",".join(str(tx_info) for tx_info in txs_info)
    )

    node_type = transaction_service.node.NODE_TYPE
    assert node_type is not None
    log_can_decompress_block(node_type, block_hash, missing_short_ids)


def _parse_block_eth(block_msg_bytes: Union[bytearray, memoryview]) -> Tuple[Sha256Hash, List[int], memoryview]:
    block_msg_bytes = block_msg_bytes if isinstance(block_msg_bytes, memoryview) else memoryview(block_msg_bytes)

    block_offsets = compact_block_short_ids_serializer.get_bx_block_offsets(block_msg_bytes)
    short_ids, _short_ids_bytes_len = compact_block_short_ids_serializer.deserialize_short_ids_from_buffer(
        block_msg_bytes,
        block_offsets.short_id_offset
    )

    block_bytes = block_msg_bytes[block_offsets.block_begin_offset: block_offsets.short_id_offset]

    _, _block_itm_len, block_itm_start = rlp_utils.consume_length_prefix(block_bytes, 0)
    block_itm_bytes = block_bytes[block_itm_start:]

    _, block_hdr_len, block_hdr_start = rlp_utils.consume_length_prefix(block_itm_bytes, 0)
    full_hdr_bytes = block_itm_bytes[0:block_hdr_start + block_hdr_len]

    block_hash_bytes = eth_common_utils.keccak_hash(full_hdr_bytes)
    block_hash = Sha256Hash(block_hash_bytes)

    _, block_txs_len, block_txs_start = rlp_utils.consume_length_prefix(
        block_itm_bytes, block_hdr_start + block_hdr_len
    )
    txs_bytes = block_itm_bytes[block_txs_start:block_txs_start + block_txs_len]

    return block_hash, short_ids, txs_bytes
