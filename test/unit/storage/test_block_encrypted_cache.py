from bxcommon.storage.block_encrypted_cache import BlockEncryptedCache
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.alarm_queue import AlarmQueue
from bxcommon.utils.object_hash import ObjectHash


class BlockEncryptedCacheTest(AbstractTestCase):
    ALARM_QUEUE = AlarmQueue()

    def setUp(self):
        payload = bytearray(i for i in xrange(100))
        self.sut = BlockEncryptedCache(self.ALARM_QUEUE)
        _, self.block_hash = self.sut.encrypt_and_add_payload(payload)

    def test_remove_item__bytes(self):
        self.assertTrue(self.sut.has_ciphertext_for_hash(self.block_hash))
        self.sut.remove_item(self.block_hash)
        self.assertFalse(self.sut.has_ciphertext_for_hash(self.block_hash))

    def test_remove_item__object_hash(self):
        self.assertTrue(self.sut.has_ciphertext_for_hash(self.block_hash))
        object_hash = ObjectHash(self.block_hash)
        self.sut.remove_item(object_hash)
        self.assertFalse(self.sut.has_ciphertext_for_hash(self.block_hash))

    def test_remove_item__memoryview(self):
        self.assertTrue(self.sut.has_ciphertext_for_hash(self.block_hash))
        mem_view = memoryview(self.block_hash)
        self.sut.remove_item(mem_view)
        self.assertFalse(self.sut.has_ciphertext_for_hash(self.block_hash))
