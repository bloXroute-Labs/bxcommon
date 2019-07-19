from abc import ABCMeta, abstractmethod

from bxcommon.utils.object_hash import Sha256Hash


class AbstractBlockMessage(metaclass=ABCMeta):

    @abstractmethod
    def block_hash(self) -> Sha256Hash:
        pass
