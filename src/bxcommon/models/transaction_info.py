from typing import NamedTuple, Optional, Union, List

from bxcommon.utils.object_hash import Sha256Hash


class TransactionInfo(NamedTuple):
    hash: Optional[Sha256Hash]
    contents: Optional[Union[bytearray, memoryview]]
    short_id: Optional[int]


class TransactionSearchResult(NamedTuple):
    found: List[TransactionInfo]
    missing: List[TransactionInfo]
