from bxcommon.messages.eth.serializers.block_header import BlockHeader, LondonBlockHeader
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.fixture import eth_fixtures
from bxcommon.utils import convert

import blxr_rlp as rlp


class TestBlockHeaders(AbstractTestCase):
    def test_pre_london_block_header_from_bytes(self):
        header: BlockHeader = rlp.decode(eth_fixtures.PRE_LONDON_BLOCK_HEADER, BlockHeader)

        self.assertEqual(
            eth_fixtures.PRE_LONDON_BLOCK_HASH, header.hash()
        )
        self.assertEqual(
            convert.hex_to_bytes(
                "5b300df7c29668cf450f438f0d4bb5cb144a3601d47acfb6d091ea201a3dee95"
            ),
            header.prev_hash
        )
        self.assertEqual(
            convert.hex_to_bytes(
                "1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
            ),
            header.uncles_hash
        )
        self.assertEqual(
            convert.hex_to_bytes(
                "1d30ede02573d06e994eadba6c3df3525f439d0e742b0fa19bfc7d77f208eeb1"
            ),
            header.state_root
        )

        self.assertEqual(eth_fixtures.PRE_LONDON_BLOCK_HEADER, rlp.encode(header))

    def test_london_block_header_from_bytes(self):
        # test to ensure that proper RLP sedes definitions aren't being inappropriately cached
        rlp.decode(eth_fixtures.PRE_LONDON_BLOCK_HEADER, BlockHeader)
        header: BlockHeader = rlp.decode(eth_fixtures.LONDON_BLOCK_HEADER, BlockHeader)

        self.assertEqual(eth_fixtures.LONDON_BLOCK_HASH, header.hash())
        self.assertIsInstance(header, LondonBlockHeader)
        self.assertEqual(
            convert.hex_to_bytes(
                "55bd57cbf3c2a6f17828f471dc971145377d85010909ee9aaf2951f30c7032a7"
            ),
            header.prev_hash
        )
        self.assertEqual(
            convert.hex_to_bytes(
                "1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
            ),
            header.uncles_hash
        )
        self.assertEqual(
            convert.hex_to_bytes(
                "bf7e2e9d37b18cdd5ff37c552dddcd1930a948eaae42639fe844a61655825bbb"
            ),
            header.state_root
        )
        self.assertEqual(11, header.base_fee_per_gas)
        self.assertEqual(eth_fixtures.LONDON_BLOCK_HEADER, rlp.encode(header))
