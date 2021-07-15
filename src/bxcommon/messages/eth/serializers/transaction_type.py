from enum import Enum


class EthTransactionType(Enum):
    LEGACY = 0
    ACCESS_LIST = 1
    DYNAMIC_FEE = 2

    def encode_rlp(self) -> bytes:
        return self.value.to_bytes(1, "big")
