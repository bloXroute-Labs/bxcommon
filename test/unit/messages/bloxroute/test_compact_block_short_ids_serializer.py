from bxcommon.messages.bloxroute import compact_block_short_ids_serializer
from bxcommon.test_utils.abstract_test_case import AbstractTestCase


class CompactBlockShortIdsSerializer(AbstractTestCase):

    def test_serialize_and_deserialize_short_ids(self):
        dummy_short_ids = [1, 203, 997, 890333, 5]

        expected_bytes_len = compact_block_short_ids_serializer.get_serialized_short_ids_bytes_len(dummy_short_ids)

        buffer = compact_block_short_ids_serializer.serialize_short_ids_into_bytes(dummy_short_ids)

        deserialized_short_ids, deserialized_bytes_len = compact_block_short_ids_serializer.deserialize_short_ids_from_buffer(
            buffer, 0)

        self.assertEqual(expected_bytes_len, len(buffer))
        self.assertEqual(expected_bytes_len, deserialized_bytes_len)
        self.assertEqual(dummy_short_ids, deserialized_short_ids)
