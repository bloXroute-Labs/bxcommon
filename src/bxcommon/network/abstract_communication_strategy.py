import heapq

class AbstractCommunicationStrategy(object):
    def __init__(self):
        self.connection_queue = []

    def get_server_address(self):
        raise NotImplementedError()

    def enqueue_connection(self, ip, port):
        heapq.heappush(self.connection_queue, (ip, port))

    def get_new_connection_address(self):
        if self.connection_queue:
            return heapq.heappop(self.connection_queue)

        return None

    def on_connection_added(self, connection_id, port, ip):
        """
        Method called by Multiplexer when new client connection is accepted

        :param connection_id: id of connection
        """

        raise NotImplementedError()

    def on_connection_closed(self, connection_id):
        """
        Method called by Multiplexer when connection is disconnected

        :param connection_id: id of connection
        """
        raise NotImplementedError()

    def on_receive(self, connection_id, bytes_received):
        """
        Method called by Multiplexer when bytes received from connection

        :param connection_id: id of connection
        """

        raise NotImplementedError()

    def on_send(self, connection_id):
        """
        Method called by Multiplexer when it is chance to send bytes on connection

        :param connection_id: id of connection
        :return: array of bytes
        """

        raise NotImplementedError()

    def on_sent(self, connection_id, bytes_sent):
        """
        Method called by Multiplexer after bytes sent on connection

        :param connection_id: id of connection
        """

        raise NotImplementedError()

    def on_sleep(self, triggered_by_timeout):
        """
        Method called by Multiplexer between event loops to get value for the next sleep timeout in seconds

        :param connection_id: id of connection
        :return: timeout in seconds. returns None if wait forever.
        """

        raise NotImplementedError()

    def on_first_sleep(self):
        """
        Method called by Multiplexer between event loops to get value for the next sleep timeout in seconds

        :param connection_id: id of connection
        :return: timeout in seconds. returns None if wait forever.
        """

        raise NotImplementedError()

    def on_chance_to_exit(self):
        raise NotImplementedError()

    def on_close(self):
        raise NotImplementedError()
