from abc import ABC, abstractmethod
from typing import Union, Optional


class AbstractBlockValidator(ABC):

    @abstractmethod
    def validate_block_header(
        self,
        block_header_bytes: Union[bytearray, memoryview],
        last_confirmed_block_number: Optional[int],
        last_confirmed_block_difficulty: Optional[int]
    ) -> bool:
        pass
