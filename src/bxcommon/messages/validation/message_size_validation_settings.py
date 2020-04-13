from dataclasses import dataclass


@dataclass
class MessageSizeValidationSettings:
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    max_block_size_bytes: int = None
    # pyre-fixme[8]: Attribute has type `int`; used as `None`.
    max_tx_size_bytes: int = None
