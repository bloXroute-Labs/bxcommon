from bxcommon.messages.eth.serializers.block import Block
from bxcommon.messages.eth.serializers.transaction import LegacyTransaction, AccessListTransaction
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.fixture import eth_fixtures
from bxcommon.utils.object_hash import Sha256Hash

import blxr_rlp as rlp


class TestBlock(AbstractTestCase):
    def test_berlin_block_from_bytes(self):
        block: Block = rlp.decode(eth_fixtures.BERLIN_BLOCK, Block)

        self.assertEqual(
            Sha256Hash.from_string(
                "0ad3836807aa90218884be62c8dd912fe5228aafa6fc2a7c21028e8c09bc91ef"
            ),
            block.header.hash_object(),
        )
        self.assertEqual(2, len(block.transactions))

        legacy_tx = block.transactions[0]
        self.assertIsInstance(legacy_tx, LegacyTransaction)
        self.assertEqual(
            Sha256Hash.from_string(
                "77b19baa4de67e45a7b26e4a220bccdbb6731885aa9927064e239ca232023215"
            ),
            legacy_tx.hash(),
        )

        acl_tx = block.transactions[1]
        self.assertIsInstance(acl_tx, AccessListTransaction)
        self.assertEqual(
            Sha256Hash.from_string(
                "554af720acf477830f996f1bc5d11e54c38aa40042aeac6f66cb66f9084a959d"
            ),
            acl_tx.hash(),
        )

        re_encoded = rlp.encode(block)
        self.assertEqual(block, rlp.decode(re_encoded, Block))

    def test_berlin_block_to_json(self):
        block: Block = rlp.decode(eth_fixtures.BERLIN_BLOCK, Block)
        block_json = block.to_json()

        self.assertEqual(2, len(block_json["transactions"]))

        legacy_tx = block_json["transactions"][0]
        self.assertEqual(
            "0x77b19baa4de67e45a7b26e4a220bccdbb6731885aa9927064e239ca232023215", legacy_tx["hash"]
        )
        self.assertEqual("0x0", legacy_tx["type"])
        self.assertNotIn("access_list", legacy_tx)

        acl_tx = block_json["transactions"][1]
        self.assertEqual(
            "0x554af720acf477830f996f1bc5d11e54c38aa40042aeac6f66cb66f9084a959d", acl_tx["hash"]
        )
        self.assertEqual("0x1", acl_tx["type"])
        self.assertIn("access_list", acl_tx)
