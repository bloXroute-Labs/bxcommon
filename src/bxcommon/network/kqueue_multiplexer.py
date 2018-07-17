import select

from bxcommon.network.abstract_multiplexer import AbstractMultiplexer
from bxcommon.network.socket_connection import SocketConnection


class KQueueMultiplexer(AbstractMultiplexer):

    def __init__(self, communication_strategy):
        super(KQueueMultiplexer, self).__init__(self, communication_strategy)

        self._kqueue = select.kqueue()
        self._kqueue.control([], 0, 0)


    def run(self):
        try:
            timeout = self._communication_strategy.get_next_sleep_timeout()

            while True:
                events = self._kqueue.control([], 1000, timeout)

                for event in events:
                    assert event.ident in self._socket_connections

                    socket_connection = self._socket_connections[event.ident]
                    assert isinstance(socket_connection, SocketConnection)

                    if event.filter == select.KQ_FILTER_READ and socket_connection.is_server:
                        self._handle_incoming_connections(socket_connection)

                    elif event.filter == select.KQ_FILTER_READ:
                        self._receive(socket_connection)

                    elif event.filter == select.KQ_FILTER_WRITE:
                        socket_connection.can_send = True
                        self._send(socket_connection)

                self._send_all_connections()

                timeout = self._communication_strategy.get_next_sleep_timeout()
        finally:
            self.close()

    def close(self):
        super(KQueueMultiplexer, self).close()

        self._kqueue.close()

    def _register_socket(self, socket_to_register):
            read_event = select.kevent(
                socket_to_register, select.KQ_FILTER_READ, select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR)
            write_event = select.kevent(
                socket_to_register, select.KQ_FILTER_WRITE, select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR)

            self._kqueue.control([read_event, write_event], 0, 0)