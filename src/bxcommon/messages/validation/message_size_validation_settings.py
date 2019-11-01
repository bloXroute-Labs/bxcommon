from dataclasses import dataclass


@dataclass
class MessageSizeValidationSettings:
    max_block_size_bytes: int = None
    max_tx_size_bytes: int = None
