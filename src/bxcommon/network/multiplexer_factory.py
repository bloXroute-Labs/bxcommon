from sys import platform

from bxcommon.network.abstract_communication_strategy import AbstractCommunicationStrategy
from bxcommon.network.epoll_multiplexer import EpollMultiplexer
from bxcommon.network.kqueue_multiplexer import KQueueMultiplexer


def create_multiplexer(communication_strategy):
    assert isinstance(communication_strategy, AbstractCommunicationStrategy)

    multiplexer_cls = None

    if platform.startswith("linux"):
        multiplexer_cls = EpollMultiplexer
    elif platform == "darwin":
        multiplexer_cls = KQueueMultiplexer

    if multiplexer_cls is None:
        raise NotImplementedError("Multiplexer is not implemented for platform '{0}'.".format(platform))

    return multiplexer_cls(communication_strategy)
