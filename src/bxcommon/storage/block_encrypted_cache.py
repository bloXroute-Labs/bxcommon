# TODO: these functions arent intended to be permanent, but pulling
# them out here for now for easier tests to convert these to different
# formats for symmetric encryption / hashing.
# We can probably implement some sort of EncryptionCacheProtocol that
# converts hash/payload types to avoid the copies on block_id (and so we
# can make ObjectHash the storage key), but that doesn't solve the copy
# of the payload, which is probably the mort significant part.
from bxcommon import constants
from bxcommon.storage.encrypted_cache import EncryptedCache
from bxcommon.utils.object_hash import Sha256Hash


def message_hash_to_hash_key(msg_hash) -> bytes:
    if isinstance(msg_hash, Sha256Hash):
        return bytes(msg_hash.binary)

    if isinstance(msg_hash, memoryview):
        return msg_hash.tobytes()

    return bytes(msg_hash)


def message_blob_to_ciphertext(msg_blob) -> bytes:
    return msg_blob.tobytes()


class BlockEncryptedCache(EncryptedCache):
    def __init__(self, alarm_queue) -> None:
        super(BlockEncryptedCache, self).__init__(constants.BLOCK_CACHE_TIMEOUT_S, alarm_queue)

    def decrypt_ciphertext(self, hash_key, ciphertext):
        """
        Attempts to decrypt from hash and blob from a BroadcastMessage
        :param hash_key: BroadcastMessage.block_id()
        :param ciphertext: BroadcastMessage.blob()
        :return decrypted block
        """
        return super(BlockEncryptedCache, self).decrypt_ciphertext(
            message_hash_to_hash_key(hash_key),
            message_blob_to_ciphertext(ciphertext)
        )

    def decrypt_and_get_payload(self, hash_key, encryption_key):
        """
        Attempts to decrypt from hash and key from a KeyMessage
        :param hash_key: KeyMessage.hash_key()
        :param encryption_key: KeyMessage.key()
        :return:  decrypted block
        """
        return super(BlockEncryptedCache, self).decrypt_and_get_payload(
            message_hash_to_hash_key(hash_key),
            message_blob_to_ciphertext(encryption_key)
        )

    def has_encryption_key_for_hash(self, hash_key):
        return super(BlockEncryptedCache, self).has_encryption_key_for_hash(
            message_hash_to_hash_key(hash_key),
        )

    def has_ciphertext_for_hash(self, hash_key):
        return super(BlockEncryptedCache, self).has_ciphertext_for_hash(
            message_hash_to_hash_key(hash_key),
        )

    def add_ciphertext(self, hash_key, ciphertext):
        return super(BlockEncryptedCache, self).add_ciphertext(
            message_hash_to_hash_key(hash_key),
            message_blob_to_ciphertext(ciphertext)
        )

    def add_key(self, hash_key, encryption_key):
        return super(BlockEncryptedCache, self).add_key(
            message_hash_to_hash_key(hash_key),
            message_blob_to_ciphertext(encryption_key)
        )

    def pop_ciphertext(self, hash_key):
        return super(BlockEncryptedCache, self).pop_ciphertext(
            message_hash_to_hash_key(hash_key)
        )

    def remove_item(self, hash_key):
        return super(BlockEncryptedCache, self).remove_item(
            message_hash_to_hash_key(hash_key)
        )
