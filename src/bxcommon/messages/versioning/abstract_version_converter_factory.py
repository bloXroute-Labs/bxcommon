from abc import ABCMeta, abstractmethod


class AbstractMessageConverterFactory:

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_message_converter(self, msg_type):
        """
        Returns message converter for message type
        :param msg_type: message type
        :return: message converter
        """
