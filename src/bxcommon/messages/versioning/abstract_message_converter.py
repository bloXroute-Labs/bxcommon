from abc import ABCMeta, abstractmethod

from bxcommon.messages.abstract_internal_message import AbstractInternalMessage


class AbstractMessageConverter:
    __metaclass__ = ABCMeta

    @abstractmethod
    def convert_to_older_version(self, msg: AbstractInternalMessage) -> AbstractInternalMessage:
        """
        Converts message of current protocol version to older version (version of converter)

        :param msg: message in current protocol version
        :return: converted message
        """

    @abstractmethod
    def convert_from_older_version(self, msg: AbstractInternalMessage) -> AbstractInternalMessage:
        """
        Converts message of older version (version of converter) to current protocol version

        :param msg: message in older protocol version
        :return: converted message
        """

    @abstractmethod
    def convert_first_bytes_to_older_version(self, first_msg_bytes):
        """
        Converts first bytes of message of current protocol version to older version (version of converter)

        :param first_msg_bytes: first bytes of message in current protocol version
        :return: converted message bytes
        """

    @abstractmethod
    def convert_first_bytes_from_older_version(self, first_msg_bytes):
        """
        Converts first message bytes of older version (version of converter) to current protocol version

        :param first_msg_bytes: first message bytes in older protocol version
        :return: converted message bytes
        """

    @abstractmethod
    def convert_last_bytes_to_older_version(self, last_msg_bytes):
        """
        Converts last bytes of message of current protocol version to older version (version of converter)

        :param last_msg_bytes: first bytes of message in current protocol version
        :return: converted message bytes
        """

    @abstractmethod
    def convert_last_bytes_from_older_version(self, last_msg_bytes):
        """
        Converts last message bytes of older version (version of converter) to current protocol version

        :param last_msg_bytes: first message bytes in older protocol version
        :return: converted message bytes
        """

    @abstractmethod
    def get_message_size_change_to_older_version(self):
        """
        Returns the difference in size between current protocol version and older version

        :return: message size difference
        """

    @abstractmethod
    def get_message_size_change_from_older_version(self):
        """
        Returns the difference in size between older version and current protocol version

        :return: message size difference
        """
