import unittest

import rlp

from bxcommon.messages.eth.serializers.block_header import BlockHeader
from bxcommon.test_utils import helpers
from bxcommon.utils.blockchain_utils.eth import eth_common_utils, eth_common_constants, transaction_validation_utils
from bxcommon.utils.object_hash import Sha256Hash


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

    def test_parse_tranasction(self):
        RAW_TX_HASH = "f86b01847735940082520894a2f6090c0483d6e6ac90a9c23d42e461fee2ac5188016147191f13b0008025a0784537f9801331b707ceedd5388d318d86b0bb43c6f5b32b30c9df960f596b05a042fe22aa47f2ae80cbb2c9272df2f8975c96a8a99020d8ac19d4d4b0e0b58219"
        transaction = transaction_validation_utils.parse_transaction(bytearray.fromhex(RAW_TX_HASH))
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.hash(), Sha256Hash.from_string("ffd59870844e5411f9e4043e654146b054bdcabe726a4bc4bd716049bfa54a69"))
