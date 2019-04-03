import time

from mock import MagicMock

from bxcommon.exceptions import DecryptionError
from bxcommon.storage.encrypted_cache import EncryptedCache
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.alarm_queue import AlarmQueue
from bxcommon.utils.crypto import symmetric_decrypt, KEY_SIZE


class EncryptedCacheTest(AbstractTestCase):
    ALARM_QUEUE = AlarmQueue()

    def test_encrypt_and_store(self):
        payload = bytearray(i for i in range(100))
        sut = EncryptedCache(10, self.ALARM_QUEUE)
        ciphertext, block_hash = sut.encrypt_and_add_payload(payload)

        self.assertEqual(1, len(sut))
        cache_item = sut._cache.get(block_hash)

        self.assertEqual(ciphertext, cache_item.ciphertext)
        self.assertEqual(payload, symmetric_decrypt(cache_item.key, cache_item.ciphertext))

    def test_decrypt_and_get(self):
        payload = bytearray(i for i in range(100))
        sut1 = EncryptedCache(10, self.ALARM_QUEUE)
        ciphertext, block_hash = sut1.encrypt_and_add_payload(payload)
        key = sut1.get_encryption_key(block_hash)

        sut2 = EncryptedCache(10, self.ALARM_QUEUE)
        sut2.add_ciphertext(block_hash, ciphertext)
        decrypted = sut2.decrypt_and_get_payload(block_hash, key)

        self.assertEqual(payload, decrypted)

    def test_decrypt_ciphertext(self):
        payload = bytearray(i for i in range(100))
        sut1 = EncryptedCache(10, self.ALARM_QUEUE)
        ciphertext, block_hash = sut1.encrypt_and_add_payload(payload)
        key = sut1.get_encryption_key(block_hash)

        sut2 = EncryptedCache(10, self.ALARM_QUEUE)
        sut2.add_key(block_hash, key)
        decrypted = sut2.decrypt_ciphertext(block_hash, ciphertext)

        self.assertEqual(payload, decrypted)

    def test_cant_decrypt_incomplete_content(self):
        ciphertext = b"foobar"
        hash_key = b"baz"

        sut1 = EncryptedCache(10, self.ALARM_QUEUE)
        sut1.add_ciphertext(hash_key, ciphertext)

        self.assertIsNone(sut1.decrypt_ciphertext(hash_key, ciphertext))

    def test_cant_decrypt_wrong_keys(self):
        ciphertext = b"foobar" * 50  # ciphertext needs to be long enough to contain a nonce
        hash_key = b"bbaz"
        bad_encryption_key = b"q" * KEY_SIZE

        sut1 = EncryptedCache(10, self.ALARM_QUEUE)
        sut1.add_ciphertext(hash_key, ciphertext)
        sut1.add_key(hash_key, bad_encryption_key)

        self.assertIsNone(sut1.decrypt_ciphertext(hash_key, ciphertext))

    def test_cache_cleanup(self):
        ciphertext = b"foobar"
        hash_key = b"baz"

        sut = EncryptedCache(10, self.ALARM_QUEUE)
        sut.add_ciphertext(hash_key, ciphertext)
        self.assertEqual(1, len(sut))

        time.time = MagicMock(return_value=time.time() + 20)
        self.ALARM_QUEUE.fire_alarms()
        self.assertEqual(0, len(sut))
