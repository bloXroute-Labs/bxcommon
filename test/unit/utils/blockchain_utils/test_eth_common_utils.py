import unittest

import blxr_rlp as rlp

from bxcommon.messages.eth.serializers.block_header import BlockHeader
from bxcommon.test_utils import helpers
from bxcommon.test_utils.fixture import eth_fixtures
from bxcommon.utils.blockchain_utils.eth import (
    eth_common_utils,
    eth_common_constants,
)


class TestEthCommonUtils(unittest.TestCase):
    def test_raw_tx_gas_price(self):
        self.assertEqual(
            2000000000,
            eth_common_utils.raw_tx_gas_price(memoryview(eth_fixtures.LEGACY_TRANSACTION), 0)
        )
        self.assertEqual(
            2000000000,
            eth_common_utils.raw_tx_gas_price(memoryview(eth_fixtures.LEGACY_TRANSACTION_EIP_2718), 0)
        )
        self.assertEqual(
            225600000000,
            eth_common_utils.raw_tx_gas_price(memoryview(eth_fixtures.ACL_TRANSACTION), 0)
        )
        self.assertEqual(
            31,
            eth_common_utils.raw_tx_gas_price(memoryview(eth_fixtures.DYNAMIC_FEE_TRANSACTION), 0)
        )

    def test_block_header_number_and_difficulty(self):
        block_header_bytes = self._create_block_header_bytes(1000, 1000000)
        block_number = eth_common_utils.block_header_number(block_header_bytes)
        difficulty = eth_common_utils.block_header_difficulty(block_header_bytes)
        self.assertEqual(1000, block_number)
        self.assertEqual(1000000, difficulty)

    def _create_block_header_bytes(self, block_number: int, difficulty: int) -> memoryview:
        block_header = BlockHeader(
            helpers.generate_bytes(eth_common_constants.BLOCK_HASH_LEN),
            helpers.generate_bytes(eth_common_constants.BLOCK_HASH_LEN),
            helpers.generate_bytes(eth_common_constants.ADDRESS_LEN),
            helpers.generate_bytes(eth_common_constants.MERKLE_ROOT_LEN),
            helpers.generate_bytes(eth_common_constants.MERKLE_ROOT_LEN),
            helpers.generate_bytes(eth_common_constants.MERKLE_ROOT_LEN),
            100,
            difficulty,
            block_number,
            3,
            4,
            1601410624,
            helpers.generate_bytes(100),
            helpers.generate_bytes(eth_common_constants.BLOCK_HASH_LEN),
            int(12345).to_bytes(eth_common_constants.BLOCK_NONCE_LEN, byteorder="big")
        )
        block_header_bytes = rlp.encode(block_header, BlockHeader)
        return memoryview(block_header_bytes)
