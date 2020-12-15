import blxr_rlp as rlp

from bxcommon.messages.eth.serializers.block_header import BlockHeader
from bxcommon.messages.eth.validation.eth_block_validator import EthBlockValidator
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.blockchain_utils.eth import eth_common_constants


class EthBlockValidatorTest(AbstractTestCase):
    def setUp(self) -> None:
        self._block_validator = EthBlockValidator()
        self._block_header = self._create_block_header(1000, 1000)
        self._block_header_bytes = memoryview(rlp.encode(self._block_header))

    def test_valid_block_1(self):
        is_valid, block_hash, _reason = self._block_validator.validate_block_header(
            self._block_header_bytes, 1000, 1000
        )
        self.assertTrue(is_valid)
        self.assertEqual(self._block_header.hash_object(), block_hash)

    def test_valid_block_2(self):
        is_valid, block_hash, _reason = self._block_validator.validate_block_header(
            self._block_header_bytes, 1200, 901
        )
        self.assertTrue(is_valid)
        self.assertEqual(self._block_header.hash_object(), block_hash)

    def test_valid_block_3(self):
        is_valid, block_hash, _reason = self._block_validator.validate_block_header(
            self._block_header_bytes, 991, 800
        )
        self.assertTrue(is_valid)
        self.assertEqual(self._block_header.hash_object(), block_hash)

    def test_invalid_block_number(self):
        is_valid, block_hash, reason = self._block_validator.validate_block_header(
            self._block_header_bytes, 899, 1000
        )
        self.assertFalse(is_valid)
        self.assertEqual(self._block_header.hash_object(), block_hash)
        self.assertEqual("Reason(s) for failure: invalid number", reason)

    def test_invalid_difficulty(self):
        is_valid, block_hash, reason = self._block_validator.validate_block_header(
            self._block_header_bytes, 1000, 1150
        )
        self.assertFalse(is_valid)
        self.assertEqual(self._block_header.hash_object(), block_hash)
        self.assertEqual("Reason(s) for failure: invalid difficulty", reason)

    def test_no_last_confirmed_info(self):
        is_valid, block_hash, _reason = self._block_validator.validate_block_header(
            self._block_header_bytes, None, None
        )
        self.assertTrue(is_valid)
        self.assertIsNone(block_hash)

    def _create_block_header(self, block_number: int, difficulty: int) -> BlockHeader:
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
        return block_header
