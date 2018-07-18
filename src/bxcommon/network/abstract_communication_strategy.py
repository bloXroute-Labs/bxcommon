class AbstractCommunicationStrategy(object):
    def add_connection(self, connection_id):
        """
        Method called by Multiplexer when new client connection is accepted

        :param connection_id: id of connection
        """

        raise NotImplementedError()

    def remove_connection(self, connection_id):
        """
        Method called by Multiplexer when connection is disconnected

        :param connection_id: id of connection
        """
        raise NotImplementedError()

    def process_received_bytes(self, connection_id, bytes):
        """
        Method called by Multiplexer when bytes received from connection

        :param connection_id: id of connection
        """

        raise NotImplementedError()

    def get_next_bytes_to_send(self, connection_id):
        """
        Method called by Multiplexer when it is chance to send bytes on connection

        :param connection_id: id of connection
        :return: array of bytes
        """

        raise NotImplementedError()

    def advance_sent_bytes(self, connection_id, bytes_sent):
        """
        Method called by Multiplexer after bytes sent on connection

        :param connection_id: id of connection
        """

        raise NotImplementedError()

    def get_next_sleep_timeout(self):
        """
        Method called by Multiplexer between event loops to get value for the next sleep timeout in seconds

        :param connection_id: id of connection
        :return: timeout in seconds. returns None if wait forever.
        """

        raise NotImplementedError()

    def is_shutdown_requested(self):
        raise NotImplementedError()
    
    def close(self):
        raise NotImplementedError()
