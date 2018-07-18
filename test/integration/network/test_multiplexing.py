import os
import unittest
from threading import Thread

from bxcommon.network.abstract_communication_strategy import AbstractCommunicationStrategy
from bxcommon.network.multiplexer_factory import create_multiplexer
from bxcommon.utils import logger


class SenderCommunicationStrategy(AbstractCommunicationStrategy):
    def __init__(self, send_bytes):
        self.send_bytes = send_bytes
        self.memory_view = memoryview(self.send_bytes)
        self.bytes_sent = 0
        self.finished_sending = False
        self.closed = False

    def add_connection(self, connection_id):
        pass

    def remove_connection(self, connection_id):
        pass

    def process_received_bytes(self, client_id, bytes):
        pass

    def get_next_bytes_to_send(self, connection_id):
        if self.bytes_sent >= len(self.send_bytes):
            logger.debug("All bytes sent. Total bytes sent {0}".format(len(self.send_bytes)))
            self.finished_sending = True

        return self.memory_view[self.bytes_sent:]

    def advance_sent_bytes(self, connection_id, bytes_sent):
        self.bytes_sent += bytes_sent

    def get_next_sleep_timeout(self):
        return None

    def is_shutdown_requested(self):
        return self.finished_sending

    def close(self):
        self.closed = True


class ReceiverCommunicationStrategy(AbstractCommunicationStrategy):
    def __init__(self):
        self.connections = []
        self.receive_buffers = {}
        self.finished_receiving = False
        self.closed = False

    def add_connection(self, connection_id):
        logger.debug("Client connected. Connection id {0}".format(connection_id))
        self.connections.append(connection_id)
        self.receive_buffers[connection_id] = bytearray(0)

    def remove_connection(self, connection_id):
        logger.debug("Client is disconnected. Received {0} bytes from the client {1}"
                     .format(len(self.receive_buffers[connection_id]), connection_id))
        self.finished_receiving = True

    def process_received_bytes(self, connection_id, bytes):
        self.receive_buffers[connection_id] += bytes

    def get_next_bytes_to_send(self, connection_id):
        pass

    def advance_sent_bytes(self, connection_id, bytes_sent):
        pass

    def get_next_sleep_timeout(self):
        None

    def is_shutdown_requested(self):
        return self.finished_receiving

    def close(self):
        self.closed = True


class MultiplexingTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logger.log_init(None, use_stdout=True)

    @classmethod
    def tearDownClass(cls):
        logger.log_close()

    def test_multiplexing(self):

        receiver_strategy = ReceiverCommunicationStrategy()
        receiver_multiplexer = create_multiplexer(receiver_strategy)
        receiver_thread = Thread(target=receiver_multiplexer.run)

        send_bytes_length = 10000
        send_bytes = bytearray(0)
        send_bytes.extend(os.urandom(send_bytes_length))

        sender_strategy = SenderCommunicationStrategy(send_bytes)
        sender_multiplexer = create_multiplexer(sender_strategy)

        try:
            receiver_multiplexer.start_server(8001)
            receiver_thread.start()

            sender_multiplexer.connect_to_server('0.0.0.0', 8001)
            sender_multiplexer.run()

            receiver_thread.join()

            self.assertTrue(sender_strategy.bytes_sent, send_bytes_length)

            self.assertTrue(len(receiver_strategy.connections), 1)
            bytes_received = receiver_strategy.receive_buffers[receiver_strategy.connections[0]]
            self.assertEqual(bytes_received, send_bytes)

            self.assertTrue(sender_strategy.is_shutdown_requested())
            self.assertTrue(receiver_strategy.is_shutdown_requested)
            self.assertTrue(sender_strategy.closed)
            self.assertTrue(receiver_strategy.closed)
        finally:
            receiver_multiplexer.close()
            sender_multiplexer.close()

            if receiver_thread.is_alive():
                receiver_thread.join()







