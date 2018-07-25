import os
import unittest
from threading import Thread

from bxcommon.network.abstract_communication_strategy import AbstractCommunicationStrategy
from bxcommon.network.multiplexer_factory import create_multiplexer
from bxcommon.utils import logger


class SenderCommunicationStrategy(AbstractCommunicationStrategy):
    def __init__(self, send_bytes):
        super(SenderCommunicationStrategy, self).__init__()

        self.send_bytes = send_bytes
        self.memory_view = memoryview(self.send_bytes)
        self.bytes_sent = 0
        self.finished_sending = False
        self.closed = False
        self.timeout_triggered_loops = 0
        self.initialized = False

    def get_server_address(self):
        return ('0.0.0.0', 8001)

    def get_peers_addresses(self):
        return [('0.0.0.0', 8002)]

    def on_connection_added(self, connection_id, port, ip, from_me):
        pass

    def on_connection_initialized(self, connection_id):
        self.initialized = True

    def on_connection_closed(self, connection_id):
        pass

    def on_bytes_received(self, client_id, bytes):
        pass

    def get_bytes_to_send(self, connection_id):
        print("Sender: get_next_bytes_to_send called. connection id {0}".format(connection_id))
        if self.bytes_sent >= len(self.send_bytes):
            logger.debug("All bytes sent. Total bytes sent {0}".format(len(self.send_bytes)))
            self.finished_sending = True

        return self.memory_view[self.bytes_sent:]

    def on_bytes_sent(self, connection_id, bytes_sent):
        print("Sender: advance_sent_bytes called. connection id {0}. bytes sent {1}".format(connection_id, bytes_sent))
        self.bytes_sent += bytes_sent

    def get_sleep_timeout(self, triggered_by_timeout, first_call=False):
        print("Sender: get_next_sleep_timeout called.")

        if triggered_by_timeout:
            self.timeout_triggered_loops += 1
        return 1

    def force_exit(self):
        print("Sender: is_shutdown_requested called.")
        return self.finished_sending and self.timeout_triggered_loops > 0

    def close(self):
        print("Sender: close called.")
        self.closed = True


class ReceiverCommunicationStrategy(AbstractCommunicationStrategy):
    def __init__(self):
        super(ReceiverCommunicationStrategy, self).__init__()

        self.connections = []
        self.receive_buffers = {}
        self.finished_receiving = False
        self.closed = False
        self.initialized = False

        self.timeout_triggered_loops = 0

    def get_server_address(self):
        return ('0.0.0.0', 8002)

    def get_peers_addresses(self):
        return None

    def on_connection_added(self, connection_id, port, ip, from_me):
        print("Receiver: add_connection called. Connection id {0}".format(connection_id))
        self.connections.append(connection_id)
        self.receive_buffers[connection_id] = bytearray(0)

    def on_connection_initialized(self, connection_id):
        self.initialized = True

    def on_connection_closed(self, connection_id):
        print("Receiver: remove_connection called.".format(connection_id))
        self.finished_receiving = True

    def on_bytes_received(self, connection_id, bytes_received):
        print("Receiver: process_received_bytes called. {0} bytes received from connection {1}"
              .format(len(bytes_received), connection_id))
        self.receive_buffers[connection_id] += bytes_received

    def get_bytes_to_send(self, connection_id):
        pass

    def on_bytes_sent(self, connection_id, bytes_sent):
        pass

    def get_sleep_timeout(self, triggered_by_timeout, first_call=False):
        print("Receiver: get_sleep_timeout called.")

        if triggered_by_timeout:
            self.timeout_triggered_loops += 1

        return None

    def force_exit(self):
        print("Receiver: is_shutdown_requested called.")
        return self.finished_receiving

    def close(self):
        print("Receiver: close called.")
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
            print("Starting event loop on receiver")
            receiver_thread.start()

            print("Starting event loop on sender")
            sender_multiplexer.run()

            receiver_thread.join()

            self.assertTrue(sender_strategy.bytes_sent, send_bytes_length)

            self.assertTrue(len(receiver_strategy.connections), 1)
            bytes_received = receiver_strategy.receive_buffers[receiver_strategy.connections[0]]
            self.assertEqual(bytes_received, send_bytes)

            self.assertTrue(sender_strategy.force_exit())
            self.assertTrue(receiver_strategy.force_exit)
            self.assertTrue(sender_strategy.closed)
            self.assertTrue(receiver_strategy.closed)
            self.assertTrue(sender_strategy.initialized)
            self.assertTrue(receiver_strategy.initialized)
            self.assertTrue(sender_strategy.timeout_triggered_loops > 0)
            self.assertEqual(receiver_strategy.timeout_triggered_loops, 0)
        finally:
            receiver_multiplexer.close()
            sender_multiplexer.close()

            if receiver_thread.is_alive():
                receiver_thread.join()
