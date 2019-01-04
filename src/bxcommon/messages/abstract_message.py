from abc import ABCMeta, abstractmethod


class AbstractMessage(object):
    __metaclass__ = ABCMeta

    HEADER_LENGTH = 0

    @classmethod
    @abstractmethod
    def unpack(cls, buf):
        """
        Unpack buffer into command, metadata (e.g. magic number, checksum), and payload.
        """
        pass

    @classmethod
    @abstractmethod
    def validate_payload(cls, buf, unpacked_args):
        """
        Validates unpacked content.
        """
        pass

    @classmethod
    @abstractmethod
    def initialize_class(cls, cls_type, buf, unpacked_args):
        """
        Initialize message class with arguments. Returns cls_type instance.
        """
        pass

    def should_log_debug(self):
        return False

