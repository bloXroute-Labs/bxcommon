from typing import Optional, TYPE_CHECKING, Any, Union, Iterator

from dataclasses import dataclass
from bxcommon.utils.object_hash import Sha256Hash


if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports,cyclic-import
    from task_pool_executor import Sha256 as tpe_Sha256
else:
    tpe_Sha256 = Any

TransactionCacheKeyType = Union[Sha256Hash, bytes, bytearray, memoryview, str, tpe_Sha256]


@dataclass()
class TransactionKey:
    transaction_hash: Sha256Hash
    _transaction_cache_key: Optional[TransactionCacheKeyType] = None
    _lazy_transaction_cache_key: Optional[Iterator[TransactionCacheKeyType]] = None

    @property
    def transaction_cache_key(self) -> TransactionCacheKeyType:
        if self._transaction_cache_key is None:
            lazy_transaction_cache_key = self._lazy_transaction_cache_key
            assert lazy_transaction_cache_key is not None
            self._transaction_cache_key = next(lazy_transaction_cache_key)
        transaction_cache_key = self._transaction_cache_key
        assert transaction_cache_key is not None
        return transaction_cache_key

    def __repr__(self):
        if isinstance(self.transaction_hash, Sha256Hash):
            return self.transaction_hash.binary.hex()
        else:
            return str(self.transaction_hash)
