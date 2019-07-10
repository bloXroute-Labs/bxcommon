from dataclasses import dataclass


@dataclass
class MessageValidationSettings:
    max_block_size_bytes: int = None
    max_tx_size_bytes: int = None
