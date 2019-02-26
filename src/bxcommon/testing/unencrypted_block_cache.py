from bxcommon.constants import NULL_ENCRYPT_REPEAT_VALUE
from bxcommon.storage.block_encrypted_cache import BlockEncryptedCache
from bxcommon.storage.encrypted_cache import EncryptionCacheItem
from bxcommon.utils import crypto
from bxcommon.utils.crypto import KEY_SIZE


class UnencryptedCacheItem(EncryptionCacheItem):
    def decrypt(self):
        self.payload = self.ciphertext
        return bytearray(self.ciphertext)


class UnencryptedCache(BlockEncryptedCache):
    NO_ENCRYPT_KEY = NULL_ENCRYPT_REPEAT_VALUE * KEY_SIZE

    def encrypt_and_add_payload(self, payload):
        block_hash = crypto.double_sha256(payload)
        self._add(block_hash, self.NO_ENCRYPT_KEY, payload, payload)
        return payload, block_hash

    def _add(self, hash_key, encryption_key, ciphertext, payload):
        self._cache[hash_key] = UnencryptedCacheItem(encryption_key, ciphertext, payload)
