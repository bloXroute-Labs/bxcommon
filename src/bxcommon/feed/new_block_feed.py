from typing import NamedTuple

from bxcommon import constants
from bxcommon.utils import convert
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.feed.feed import Feed


class RawBlockFeedEntry:
    hash: str
    block: str

    # pylint: disable=redefined-builtin
    def __init__(
        self,
        hash: Sha256Hash,
        block: memoryview
    ) -> None:
        self.hash = str(hash)
        self.block = convert.bytes_to_hex(block)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, RawBlockFeedEntry)
            and other.hash == self.hash
            and other.block == self.block
        )


class RawBlock(NamedTuple):
    hash: Sha256Hash
    block: memoryview


class NewBlockFeed(Feed[RawBlockFeedEntry, RawBlock]):
    NAME = "newBlocks"
    FIELDS = ["hash", "block"]
    ALL_FIELDS = FIELDS

    def __init__(self, network_num: int = constants.ALL_NETWORK_NUM,) -> None:
        super().__init__(self.NAME, network_num=network_num)

    def serialize(self, raw_message: RawBlock) -> RawBlockFeedEntry:
        return RawBlockFeedEntry(raw_message.hash, raw_message.block)
