from dataclasses import dataclass
from typing import Union, Optional

from bxcommon.messages.eth.validation.abstract_block_validator import AbstractBlockValidator, \
    BlockValidationResult
from bxcommon.utils.blockchain_utils.eth import eth_common_utils, rlp_utils, eth_common_constants
from bxcommon.utils.object_hash import Sha256Hash
from bxutils import logging

logger = logging.get_logger(__name__)


@dataclass
class BlockParameters:
    block_hash: Sha256Hash
    block_number: int
    difficulty: int
    mix_hash: Union[bytearray, memoryview]
    proof_of_work_nonce: Union[bytearray, memoryview]


class EthBlockValidator(AbstractBlockValidator):
    def validate_block_header(
        self,
        block_header_bytes: Union[bytearray, memoryview],
        last_confirmed_block_number: Optional[int],
        last_confirmed_block_difficulty: Optional[int]
    ) -> BlockValidationResult:
        if last_confirmed_block_difficulty is None or last_confirmed_block_number is None:
            logger.debug("Skipping block validation because do not have information about last confirmed block")
            return BlockValidationResult(True, None, None)
        block_parameters = self._parse_block_parameters(block_header_bytes)

        valid_block_number = self._validate_block_number(block_parameters, last_confirmed_block_number)
        valid_difficulty = self._validate_block_difficulty(block_parameters, last_confirmed_block_difficulty)
        valid = valid_block_number and valid_difficulty

        if valid:
            logger.debug("Successfully validate block {}", block_parameters.block_hash)
            reason = None
        else:
            logger.info("Validation failed for block {}. Skipping the block.", block_parameters.block_hash)
            reasons = []
            if not valid_block_number:
                reasons.append("invalid number")
            if not valid_difficulty:
                reasons.append("invalid difficulty")
            reason = f"Reason(s) for failure: {', '.join(reasons)}"

        return BlockValidationResult(valid, block_parameters.block_hash, reason)

    def _parse_block_parameters(self, full_block_header_bytes: Union[bytearray, memoryview]) -> BlockParameters:
        _, block_header_len, block_header_start = rlp_utils.consume_length_prefix(full_block_header_bytes, 0)
        block_header_bytes = full_block_header_bytes[block_header_start:block_header_start + block_header_len]
        block_hash = self._get_block_hash(full_block_header_bytes)
        offset = eth_common_constants.FIXED_LENGTH_FIELD_OFFSET
        difficulty, difficulty_length = rlp_utils.decode_int(block_header_bytes, offset)
        offset += difficulty_length
        number, _ = rlp_utils.decode_int(block_header_bytes, offset)
        _gas_limit, gas_limit_length = rlp_utils.decode_int(block_header_bytes, offset)
        offset += gas_limit_length
        _gas_used, gas_used_length = rlp_utils.decode_int(block_header_bytes, offset)
        offset += gas_used_length
        _timestamp, timestamp_length = rlp_utils.decode_int(block_header_bytes, offset)
        offset += timestamp_length
        _, extra_data_length, extra_data_start = rlp_utils.consume_length_prefix(block_header_bytes, offset)
        offset = extra_data_start + extra_data_length
        _, mix_hash_length, mix_hash_start = rlp_utils.consume_length_prefix(block_header_bytes, offset)
        mix_hash = block_header_bytes[mix_hash_start:mix_hash_start + mix_hash_length]
        offset = mix_hash_start + mix_hash_length
        _, nonce_length, nonce_start = rlp_utils.consume_length_prefix(block_header_bytes, offset)
        nonce = block_header_bytes[nonce_start:nonce_start + nonce_length]

        return BlockParameters(block_hash, number, difficulty, mix_hash, nonce)

    def _get_block_hash(self, block_header_bytes: Union[bytearray, memoryview]) -> Sha256Hash:
        raw_hash = eth_common_utils.keccak_hash(memoryview(block_header_bytes))
        return Sha256Hash(raw_hash)

    def _validate_block_number(self, block_parameters: BlockParameters, last_confirmed_block_number: int) -> bool:
        block_number = block_parameters.block_number
        block_hash = block_parameters.block_hash

        valid = block_number - last_confirmed_block_number <= eth_common_constants.MAX_FUTURE_BLOCK_NUMBER
        if not valid:
            logger.debug(
                "Block {} is invalid. Block number {} is way ahead of the last confirmed block {}.",
                block_hash, block_number, last_confirmed_block_number
            )

        return valid

    def _validate_block_difficulty(
        self, block_parameters: BlockParameters, last_confirmed_block_difficulty: int
    ) -> bool:
        block_difficulty = block_parameters.difficulty
        block_hash = block_parameters.block_hash

        max_difficulty_change = int(
            last_confirmed_block_difficulty / 100 * eth_common_constants.MAX_DIFFICULTY_CHANGE_PERCENT
        )
        valid = last_confirmed_block_difficulty - block_difficulty < max_difficulty_change
        if not valid:
            logger.debug(
                "Block {} is invalid. Block difficulty {} is significantly lower than "
                "the difficulty of last confirmed block {}, with max difficulty change {}.",
                block_hash, block_difficulty, last_confirmed_block_difficulty, max_difficulty_change
            )
        return valid
