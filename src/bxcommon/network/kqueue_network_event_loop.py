import select
import socket
from typing import Tuple

from bxcommon import constants
from bxcommon.network.abstract_network_event_loop import AbstractNetworkEventLoop
from bxcommon.network.socket_connection_state import SocketConnectionState


class KQueueNetworkEventLoop(AbstractNetworkEventLoop):
    """
    Implementation of network event loop for MacOS that uses KQueue

    Documentation for 'select' and 'KQueue' - https://docs.python.org/2/library/select.html
    """

    def __init__(self, node):
        super(KQueueNetworkEventLoop, self).__init__(node)

        self._kqueue = select.kqueue()

        # initialize kqueue with empty list of events. do not pull any events and continue immediately
        self._kqueue.control([], 0, 0)

    def close(self):
        super(KQueueNetworkEventLoop, self).close()

        self._kqueue.close()

    def _process_events(self, timeout: float) -> int:

        # get all available events from kqueue or wait until timeout. do not add any new events ([] is empty).
        events = self._kqueue.control([], constants.MAX_KQUEUE_EVENTS_COUNT, timeout)

        receive_connections = []

        # Process new connections and send events before receive
        for event in events:
            assert event.ident in self._socket_connections

            socket_connection = self._socket_connections[event.ident]

            if event.filter == select.KQ_FILTER_READ and socket_connection.is_server:
                self._handle_incoming_connections(socket_connection)

            elif event.filter == select.KQ_FILTER_WRITE and not event.flags & select.KQ_EV_EOF:
                self._send_on_socket(socket_connection)

            elif event.filter == select.KQ_FILTER_READ:
                receive_connections.append(socket_connection)

        # Process receive events in the end
        for socket_connection in receive_connections:
            if not socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE:
                if self._node.on_input_received(socket_connection.fileno()):
                    socket_connection.receive()

        return len(events)

    def _register_socket(
        self,
        new_socket: socket.socket,
        address: Tuple[str, int],
        is_server: bool = False,
        initialized: bool = True,
        from_me: bool = False,
    ):
        super(KQueueNetworkEventLoop, self)._register_socket(new_socket, address, is_server, initialized, from_me)

        read_event = select.kevent(
            new_socket, select.KQ_FILTER_READ, select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR,
        )
        write_event = select.kevent(
            new_socket, select.KQ_FILTER_WRITE, select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR,
        )

        # add new events to listen. do not pull any events from kqeue and continue immediately.
        self._kqueue.control([read_event, write_event], 0, 0)
