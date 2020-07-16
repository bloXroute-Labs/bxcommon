from nacl.exceptions import CryptoError

from bxcommon.exceptions import DecryptionError
from bxcommon.utils import crypto, convert
from bxcommon.utils.crypto import symmetric_decrypt, symmetric_encrypt
from bxcommon.utils.expiration_queue import ExpirationQueue
from bxutils import log_messages
from bxutils import logging

logger = logging.get_logger(__name__)


class EncryptionCacheItem:
    def __init__(self, key, ciphertext, payload) -> None:
        self.key = key
        self.ciphertext = ciphertext
        self.payload = payload

    def decrypt(self):
        if self.key is None or self.ciphertext is None:
            raise DecryptionError("Tried decryption without a key and ciphertext. Can't do that.")
        try:
            self.payload = symmetric_decrypt(self.key, self.ciphertext)
            return bytearray(self.payload)
        except (ValueError, CryptoError) as _e:
            # TODO: need to handle decryption errors, e.g. fake key or ciphertext
            raise DecryptionError("Decryption failed. Key does not match ciphertext.")


class EncryptedCache:
    """
    Storage for in-progress received or sent encrypted blocks.
    """

    def __init__(self, expiration_time_s, alarm_queue) -> None:
        self._cache = {}
        self._expiration_queue = ExpirationQueue(expiration_time_s)
        self._expiration_time_s = expiration_time_s
        self._alarm_queue = alarm_queue

    def encrypt_and_add_payload(self, payload):
        """
        Encrypts payload, computing a hash and storing it along with the key for later release.
        If encryption is disabled for dev, store ciphertext identical to hash_key.
        """
        key, ciphertext = symmetric_encrypt(bytes(payload))
        hash_key = crypto.double_sha256(ciphertext)
        self._add(hash_key, key, ciphertext, payload)
        return ciphertext, hash_key

    def add_ciphertext(self, hash_key, ciphertext):
        if hash_key in self._cache:
            self._cache[hash_key].ciphertext = ciphertext
        else:
            self._add(hash_key, None, ciphertext, None)

    def add_key(self, hash_key, encryption_key):
        if hash_key in self._cache:
            self._cache[hash_key].key = encryption_key
        else:
            self._add(hash_key, encryption_key, None, None)

    def decrypt_and_get_payload(self, hash_key, encryption_key):
        """
        Retrieves and decrypts stored ciphertext.
        Returns None if unable to decrypt.
        """
        cache_item = self._cache[hash_key]
        cache_item.key = encryption_key
        return self._safe_decrypt_item(cache_item, hash_key)

    def decrypt_ciphertext(self, hash_key, ciphertext):
        """
        Retrieves and decrypts ciphertext with stored key info. Stores info in cache.
        Returns None if unable to decrypt.
        """

        cache_item = self._cache[hash_key]
        cache_item.ciphertext = ciphertext

        return self._safe_decrypt_item(cache_item, hash_key)

    def get_encryption_key(self, hash_key):
        return self._cache[hash_key].key

    def pop_ciphertext(self, hash_key):
        return self._cache.pop(hash_key).ciphertext

    def has_encryption_key_for_hash(self, hash_key):
        return hash_key in self._cache and self._cache[hash_key].key is not None

    def has_ciphertext_for_hash(self, hash_key):
        return hash_key in self._cache and self._cache[hash_key].ciphertext is not None

    def hash_keys(self):
        return self._cache.keys()

    def encryption_items(self):
        return self._cache.values()

    def remove_item(self, hash_key):
        if hash_key in self._cache:
            del self._cache[hash_key]

    def _add(self, hash_key, encryption_key, ciphertext, payload):
        self._cache[hash_key] = EncryptionCacheItem(encryption_key, ciphertext, payload)
        self._expiration_queue.add(hash_key)
        self._alarm_queue.register_approx_alarm(self._expiration_time_s * 2, self._expiration_time_s,
                                                self._cleanup_old_cache_items)

    def _cleanup_old_cache_items(self):
        self._expiration_queue.remove_expired(remove_callback=self.remove_item)

    def __iter__(self):
        return iter(self._cache)

    def __len__(self):
        return len(self._cache)

    def _safe_decrypt_item(self, cache_item, hash_key):
        try:
            return cache_item.decrypt()
        except DecryptionError:
            failed_ciphertext = self.pop_ciphertext(hash_key)
            logger.warning(log_messages.DECRYPTION_FAILED,
                           convert.bytes_to_hex(hash_key), convert.bytes_to_hex(failed_ciphertext[-4:]))
            return None
