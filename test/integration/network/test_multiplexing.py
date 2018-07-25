import time
import unittest
from threading import Thread

from bxcommon.network.abstract_communication_strategy import AbstractCommunicationStrategy
from bxcommon.network.multiplexer_factory import create_multiplexer
from bxcommon.test_utils.helpers import generate_bytearray
from bxcommon.utils import logger


class TestCommunicationStrategy(AbstractCommunicationStrategy):
    def __init__(self, port, peers_ports, timeout=None, send_bytes=None):
        super(TestCommunicationStrategy, self).__init__()

        self.port = port
        self.peers_ports = peers_ports
        self.timeout = timeout

        self.initialized = False
        self.closed = False
        self.finished_sending = True
        self.ready_to_close = False

        self.connections = []

        self.send_bytes = send_bytes if send_bytes is not None else bytearray(0)
        self.memory_view = memoryview(self.send_bytes)
        self.bytes_sent = 0

        self.receive_buffers = {}

        self.timeout_triggered_loops = 0

    def get_server_address(self):
        return ('0.0.0.0', self.port)

    def get_peers_addresses(self):
        peer_addresses = []

        for peer_port in self.peers_ports:
            peer_addresses.append(('0.0.0.0', peer_port))

        return peer_addresses

    def on_connection_added(self, connection_id, port, ip, from_me):
        print("Node {0}: Add_connection call. Connection id {1}".format(self.port, connection_id))
        self.connections.append((connection_id, port, ip, from_me))
        self.receive_buffers[connection_id] = bytearray(0)

    def on_connection_initialized(self, connection_id):
        self.initialized = True

    def on_connection_closed(self, connection_id):
        print("Node {0}: on_connection_closed call. connection id {1}".format(self.port, connection_id))
        self.ready_to_close = True

    def get_bytes_to_send(self, connection_id):
        print("Node {0}: get_bytes_to_send call. connection id {1}".format(self.port, connection_id))
        if self.bytes_sent >= len(self.send_bytes):
            logger.debug("All bytes sent. Total bytes sent {0}".format(len(self.send_bytes)))
            self.finished_sending = True

        return self.memory_view[self.bytes_sent:]

    def on_bytes_sent(self, connection_id, bytes_sent):
        print("Node {0}: on_bytes_sent call. connection id {1}. bytes sent {2}"
              .format(self.port, connection_id, bytes_sent))
        self.bytes_sent += bytes_sent

        if len(self.send_bytes) == self.bytes_sent:
            self.ready_to_close = True

    def on_bytes_received(self, connection_id, bytes_received):
        print("Node {0}: on_bytes_received call. {1} bytes received from connection {2}"
              .format(self.port, len(bytes_received), connection_id))
        self.receive_buffers[connection_id] += bytes_received

    def get_sleep_timeout(self, triggered_by_timeout, first_call=False):
        print("Node {0}: get_sleep_timeout called.".format(self.port))

        if triggered_by_timeout:
            self.timeout_triggered_loops += 1
        return self.timeout

    def force_exit(self):
        print("Node {0}: force_exit call. Exit: {1}".format(self.port, self.ready_to_close))
        return self.ready_to_close

    def close(self):
        print("Node {0}: Close call.".format(self.port))
        self.closed = True


class MultiplexingTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logger.log_init(None, use_stdout=True)

    @classmethod
    def tearDownClass(cls):
        logger.log_close()

    def test_multiplexing__send(self):
        receiver_strategy = TestCommunicationStrategy(8001, [], 0.01)
        receiver_multiplexer = create_multiplexer(receiver_strategy)
        receiver_thread = Thread(target=receiver_multiplexer.run)

        send_bytes = generate_bytearray(1000)

        sender_strategy = TestCommunicationStrategy(8002, [8001], None, send_bytes)
        sender_multiplexer = create_multiplexer(sender_strategy)

        try:
            print("Starting event loop on receiver")
            receiver_thread.start()

            # let receiver run for 0.1 sec, more than timeout time
            time.sleep(0.1)

            sender_multiplexer.run()

            receiver_thread.join()

            self._validate_successful_run(send_bytes, sender_strategy, receiver_strategy, sender_multiplexer,
                                          receiver_multiplexer)

            # verify that sender does not have any timeout triggered loops and receiver does
            self.assertEqual(sender_strategy.timeout_triggered_loops, 0)
            self.assertTrue(receiver_strategy.timeout_triggered_loops > 0)
        finally:
            if receiver_thread.is_alive():
                receiver_thread.join()

            receiver_multiplexer.close()
            sender_multiplexer.close()

    def test_multiplexing__delayed_connect(self):
        receiver_strategy = TestCommunicationStrategy(8001, [], 0.01)
        receiver_multiplexer = create_multiplexer(receiver_strategy)
        receiver_thread = Thread(target=receiver_multiplexer.run)

        send_bytes = generate_bytearray(1000)

        sender_strategy = TestCommunicationStrategy(8002, [], 0.01, send_bytes)
        sender_multiplexer = create_multiplexer(sender_strategy)
        sender_thread = Thread(target=sender_multiplexer.run)

        try:
            print("Starting event loop on receiver")
            receiver_thread.start()

            print("Starting event loop on sender")
            sender_thread.start()

            # let threads run for 0.1 sec
            time.sleep(0.1)

            self.assertEqual(len(receiver_strategy.connections), 0)
            self.assertEqual(len(sender_strategy.connections), 0)

            # request connection while clients are running
            sender_strategy.enqueue_connection('0.0.0.0', receiver_strategy.port)

            receiver_thread.join()
            sender_thread.join()

            self._validate_successful_run(send_bytes, sender_strategy, receiver_strategy, sender_multiplexer,
                                          receiver_multiplexer)
        finally:
            if receiver_thread.is_alive():
                receiver_thread.join()

            if sender_thread.is_alive():
                sender_thread.join()

            receiver_multiplexer.close()
            sender_multiplexer.close()

    def test_multiplexing__disconnect(self):
        receiver_strategy = TestCommunicationStrategy(8001, [], 0.01)
        receiver_multiplexer = create_multiplexer(receiver_strategy)
        receiver_thread = Thread(target=receiver_multiplexer.run)

        sender_strategy = TestCommunicationStrategy(8002, [8001], 0.01)
        sender_multiplexer = create_multiplexer(sender_strategy)
        sender_thread = Thread(target=sender_multiplexer.run)

        try:
            print("Starting event loop on receiver")
            receiver_thread.start()
            sender_thread.start()

            # let threads run for 0.1 sec
            time.sleep(0.1)

            self.assertEqual(len(receiver_strategy.connections), 1)
            self.assertEqual(len(sender_strategy.connections), 1)

            # request connection while clients are running
            sender_strategy.enqueue_disconnect(sender_strategy.connections[0][0])

            # sender and receiver have to disconnect and exit
            receiver_thread.join()
            sender_thread.join()
        finally:
            if receiver_thread.is_alive():
                receiver_thread.join()

            if sender_thread.is_alive():
                sender_thread.join()

            receiver_multiplexer.close()
            sender_multiplexer.close()


    def _validate_successful_run(self, send_bytes, sender_strategy, receiver_strategy, sender_multiplexer,
                                 receiver_multiplexer):
        self.assertTrue(sender_strategy.bytes_sent, len(send_bytes))

        self.assertTrue(len(sender_strategy.connections), 1)
        self.assertTrue(len(sender_multiplexer._socket_connections), 1)
        self.assertEqual(sender_strategy.connections[0][1], '0.0.0.0')
        self.assertEqual(sender_strategy.connections[0][2], receiver_strategy.port)
        self.assertEqual(sender_strategy.connections[0][3], True)

        self.assertTrue(len(receiver_strategy.connections), 1)
        self.assertTrue(len(receiver_multiplexer._socket_connections), 1)
        self.assertEqual(receiver_strategy.connections[0][1], '127.0.0.1')
        self.assertEqual(receiver_strategy.connections[0][3], False)

        bytes_received = receiver_strategy.receive_buffers[receiver_strategy.connections[0][0]]
        self.assertEqual(bytes_received, send_bytes)

        self.assertTrue(sender_strategy.force_exit())
        self.assertTrue(receiver_strategy.force_exit)
        self.assertTrue(sender_strategy.closed)
        self.assertTrue(receiver_strategy.closed)
        self.assertTrue(sender_strategy.initialized)
        self.assertTrue(receiver_strategy.initialized)
