from abc import abstractmethod, ABC

from bxutils.logging.log_level import LogLevel


class AbstractMessage(ABC):
    HEADER_LENGTH = 0

    @classmethod
    @abstractmethod
    def unpack(cls, buf):
        """
        Unpack buffer into command, metadata (e.g. magic number, checksum), and payload.
        """

    @classmethod
    @abstractmethod
    def validate_payload(cls, buf, unpacked_args) -> None:
        """
        Validates unpacked content.
        """

    @classmethod
    @abstractmethod
    def initialize_class(cls, cls_type, buf, unpacked_args):
        """
        Initialize message class with arguments. Returns cls_type instance.
        """

    def log_level(self) -> LogLevel:
        return LogLevel.TRACE

    @abstractmethod
    def rawbytes(self) -> memoryview:
        """
        Returns raw message bytes of message.
        """
