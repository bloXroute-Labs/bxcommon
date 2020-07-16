from abc import abstractmethod

from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.utils.object_hash import Sha256Hash


class AbstractBlockMessage(AbstractMessage):

    @abstractmethod
    def block_hash(self) -> Sha256Hash:
        pass

    @abstractmethod
    def prev_block_hash(self) -> Sha256Hash:
        pass

    @abstractmethod
    def timestamp(self) -> int:
        pass

    def extra_stats_data(self) -> str:
        return ""

    @abstractmethod
    def txns(self):
        # each blockchain network returns its own list format
        pass
