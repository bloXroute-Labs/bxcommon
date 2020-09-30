import rlp

from bxcommon.messages.eth.serializers.block_header import BlockHeader
from bxcommon.messages.eth.validation.eth_block_validator import EthBlockValidator
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.blockchain_utils.eth import eth_common_constants


class EthBlockValidatorTest(AbstractTestCase):
    def setUp(self) -> None:
        self._block_validator = EthBlockValidator()
        self._block_header_bytes = self._create_block_header_bytes(1000, 1000)

    def test_valid_block_1(self):
        self.assertTrue(self._block_validator.validate_block_header(self._block_header_bytes, 1000, 1000))

    def test_valid_block_2(self):
        self.assertTrue(self._block_validator.validate_block_header(self._block_header_bytes, 1200, 901))

    def test_valid_block_3(self):
        self.assertTrue(self._block_validator.validate_block_header(self._block_header_bytes, 991, 800))

    def test_invalid_block_number(self):
        self.assertFalse(self._block_validator.validate_block_header(self._block_header_bytes, 899, 1000))

    def test_invalid_difficulty(self):
        self.assertFalse(self._block_validator.validate_block_header(self._block_header_bytes, 1000, 1150))

    def test_no_last_confirmed_info(self):
        self.assertTrue(self._block_validator.validate_block_header(self._block_header_bytes, None, None))

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

        block_header_bytes = memoryview(rlp.encode(BlockHeader.serialize(block_header)))
        return block_header_bytes
