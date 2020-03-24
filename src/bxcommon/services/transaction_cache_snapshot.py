from dataclasses import dataclass
from typing import Optional


@dataclass
class TransactionCacheSnapshot:
    serialized_transactions_details: Optional[memoryview] = None
    offset: int = 0
