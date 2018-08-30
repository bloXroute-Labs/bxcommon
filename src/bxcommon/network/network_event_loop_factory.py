from sys import platform

from bxcommon import constants
from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.network.epoll_network_event_loop import EpollNetworkEventLoop
from bxcommon.network.kqueue_network_event_loop import KQueueNetworkEventLoop


def create_event_loop(node):
    if not isinstance(node, AbstractNode):
        raise ValueError("Type inherited from AbstractNode is expected.")

    event_loop_class = None

    if platform.startswith(constants.PLATFORM_LINUX):
        event_loop_class = EpollNetworkEventLoop
    elif platform == constants.PLATFORM_MAC:
        event_loop_class = KQueueNetworkEventLoop

    if event_loop_class is None:
        raise NotImplementedError("Multiplexer is not implemented for platform '{0}'.".format(platform))

    return event_loop_class(node)
