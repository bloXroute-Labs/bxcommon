from abc import ABC, abstractmethod
from typing import Union, Optional, NamedTuple

from bxcommon.utils.object_hash import Sha256Hash


class BlockValidationResult(NamedTuple):
    is_valid: bool
    block_hash: Optional[Sha256Hash]
    reason: Optional[str]


class AbstractBlockValidator(ABC):
    @abstractmethod
    def validate_block_header(
        self,
        block_header_bytes: Union[bytearray, memoryview],
        last_confirmed_block_number: Optional[int],
        last_confirmed_block_difficulty: Optional[int]
    ) -> BlockValidationResult:
        pass
