import select

from bxcommon.network.abstract_multiplexer import AbstractMultiplexer
from bxcommon.network.socket_connection import SocketConnection
from bxcommon.network.socket_connection_state import SocketConnectionState


class KQueueMultiplexer(AbstractMultiplexer):

    def __init__(self, communication_strategy):
        super(KQueueMultiplexer, self).__init__(communication_strategy)

        self._kqueue = select.kqueue()
        self._kqueue.control([], 0, 0)

    def close(self):
        super(KQueueMultiplexer, self).close()

        self._kqueue.close()

    def _process_events(self, timeout):
        events = self._kqueue.control([], 1000, timeout)

        for event in events:
            assert event.ident in self._socket_connections

            socket_connection = self._socket_connections[event.ident]
            assert isinstance(socket_connection, SocketConnection)

            if event.filter == select.KQ_FILTER_READ and socket_connection.is_server:
                self._handle_incoming_connections(socket_connection)

            elif event.filter == select.KQ_FILTER_READ:
                self._receive(socket_connection)

            elif event.filter == select.KQ_FILTER_WRITE and \
                    not socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE:

                if not socket_connection.state & SocketConnectionState.INITIALIZED:
                    socket_connection.set_state(SocketConnectionState.INITIALIZED)
                    self._communication_strategy.on_connection_initialized(event.ident)

                socket_connection.can_send = True
                self._send(socket_connection)

        self._send_all_connections()

        return len(events)

    def _register_socket(self, new_socket, address, is_server=False, initialized=True, from_me=False):
        super(KQueueMultiplexer, self)._register_socket(new_socket, address, is_server, initialized, from_me)

        read_event = select.kevent(
            new_socket, select.KQ_FILTER_READ, select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR)
        write_event = select.kevent(
            new_socket, select.KQ_FILTER_WRITE, select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR)

        self._kqueue.control([read_event, write_event], 0, 0)
