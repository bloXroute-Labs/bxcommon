import heapq


class AbstractCommunicationStrategy(object):
    def __init__(self):
        self.connection_queue = []

    def get_server_address(self):
        """
        Returns the address of the current server

        :return: tuple (ip, port)
        """

        raise NotImplementedError()

    def get_peers_addresses(self):
        """
        Returns list of peers addresses that multiplexer needs to connect to on start up

        :return: list of tuples (ip, port)
        """

        raise NotImplementedError()

    def enqueue_connection(self, ip, port):
        """
        Add address to the queue of outbound connections
        """

        heapq.heappush(self.connection_queue, (ip, port))

    def pop_next_connection_address(self):
        """
        Get next address from the queue of outbound connections

        :return: tuple (ip, port)
        """

        if self.connection_queue:
            return heapq.heappop(self.connection_queue)

        return None

    def on_connection_added(self, connection_id, ip, port, from_me):
        """
        Method called by Multiplexer when new client connection is accepted

        :param connection_id: id of connection
        :param ip: IP of new connection
        :param port: port of new connection
        :param from_me: flag indicating if this is outbound connection
        :return:
        """

        raise NotImplementedError()

    def on_connection_closed(self, connection_id):
        """
        Method called by Multiplexer when connection is disconnected

        :param connection_id: id of connection
        """
        raise NotImplementedError()

    def on_bytes_received(self, connection_id, bytes_received):
        """
        Method called by Multiplexer when bytes received from connection

        :param connection_id: id of connection
        """

        raise NotImplementedError()

    def get_bytes_to_send(self, connection_id):
        """
        Method called by Multiplexer when it is chance to send bytes on connection

        :param connection_id: id of connection
        :return: array of bytes
        """

        raise NotImplementedError()

    def on_bytes_sent(self, connection_id, bytes_sent):
        """
        Method called by Multiplexer after bytes sent on connection

        :param connection_id: id of connection
        """

        raise NotImplementedError()

    def get_sleep_timeout(self, triggered_by_timeout, first_call=False):
        """
        Method called by Multiplexer between event loops to get value for the next sleep timeout in seconds

        :param triggered_by_timeout: flag indicating if event loop woke up by timeout
        :param first_call: flag indicating if this is first call before starting event loop
        :return: timeout in seconds. returns None if wait forever.
        """

        raise NotImplementedError()

    def force_exit(self):
        """
        Method called by Multiplexer between event loops to check if force exit is requested

        :return: True to force exit, False otherwise
        """

        raise NotImplementedError()

    def close(self):
        """
        Close all resources used by instance
        """

        raise NotImplementedError()
