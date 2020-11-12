import unittest

import rlp

from bxcommon.messages.eth.serializers.block_header import BlockHeader
from bxcommon.test_utils import helpers
from bxcommon.utils.blockchain_utils.eth import eth_common_utils, eth_common_constants


class TestEthCommonUtils(unittest.TestCase):

    def test_raw_tx_gas_price(self):
        tx_bytes = \
            b"\xf8k" \
            b"!" \
            b"\x85\x0b\xdf\xd6>\x00" \
            b"\x82R\x08\x94" \
            b"\xf8\x04O\xf8$\xc2\xdc\xe1t\xb4\xee\x9f\x95\x8c*s\x84\x83\x18\x9e" \
            b"\x87\t<\xaf\xacj\x80\x00\x80" \
            b"!" \
            b"\xa0-\xbf,\xa9+\xae\xabJ\x03\xcd\xfa\xe3<\xbf$\x00e\xe2N|\xc9\xf7\xe2\xa9\x9c>\xdfn\x0cO\xc0\x16" \
            b"\xa0)\x11K=;\x96X}a\xd5\x00\x06eSz\xd1,\xe4>\xa1\x8c\xf8\x7f>\x0e:\xd1\xcd\x00?'?"

        self.assertEqual(51000000000, eth_common_utils.raw_tx_gas_price(memoryview(tx_bytes), 0))

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
            helpers.generate_bytes(12345)
        )
        block_header_bytes = rlp.encode(block_header, BlockHeader)
        return memoryview(block_header_bytes)

