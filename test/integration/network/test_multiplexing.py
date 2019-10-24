import time
from threading import Thread

from bxutils import logging

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.connections.node_type import NodeType
from bxcommon.network.network_event_loop_factory import create_event_loop
from bxcommon.test_utils import helpers
from bxcommon.test_utils.helpers import generate_bytearray

logger = logging.get_logger(__name__)


class TestNode(AbstractNode):
    def __init__(self, port, peers_ports, timeout=None, send_bytes=None):
        opts = helpers.get_common_opts(port)
        super(TestNode, self).__init__(opts)

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

    def send_request_for_relay_peers(self):
        pass

    def get_outbound_peer_addresses(self):
        peer_addresses = []

        for peer_port in self.peers_ports:
            peer_addresses.append(('0.0.0.0', peer_port))

        return peer_addresses

    def build_connection(self, socket_connection, ip, port, from_me=False):
        return None

    def on_connection_added(self, socket_connection, port, ip, from_me):
        fileno = socket_connection.fileno()
        print("Node {0}: Add_connection call. Fileno {1}".format(self.port, fileno))
        self.connections.append((fileno, port, ip, from_me))
        self.receive_buffers[fileno] = bytearray(0)

    def on_connection_initialized(self, fileno):
        self.initialized = True

    def on_connection_closed(self, fileno):
        print("Node {0}: on_connection_closed call. Fileno {1}".format(self.port, fileno))
        self.ready_to_close = True

    def get_bytes_to_send(self, fileno):
        print("Node {0}: get_bytes_to_send call. Fileno {1}".format(self.port, fileno))
        if self.bytes_sent >= len(self.send_bytes):
            logger.debug("All bytes sent. Total bytes sent {0}".format(len(self.send_bytes)))
            self.finished_sending = True

        return self.memory_view[self.bytes_sent:]

    def on_bytes_sent(self, fileno, bytes_sent):
        print("Node {0}: on_bytes_sent call. Fileno {1}. bytes sent {2}"
              .format(self.port, fileno, bytes_sent))
        self.bytes_sent += bytes_sent

        if len(self.send_bytes) == self.bytes_sent:
            self.ready_to_close = True

    def on_bytes_received(self, fileno: int, bytes_received: bytearray):
        print("Node {0}: on_bytes_received call. {1} bytes received from connection {2}"
              .format(self.port, len(bytes_received), fileno))
        self.receive_buffers[fileno] += bytes_received

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

    def on_input_received(self, file_no: int) -> bool:
        return True


class MultiplexingTest(AbstractTestCase):

    def test_multiplexing__send(self):
        receiver_node = TestNode(8001, [], 0.01)
        receiver_event_loop = create_event_loop(receiver_node)
        receiver_thread = Thread(target=receiver_event_loop.run)

        send_bytes = generate_bytearray(1000)

        sender_node = TestNode(8002, [8001], None, send_bytes)
        sender_event_loop = create_event_loop(sender_node)

        try:
            print("Starting event loop on receiver")
            receiver_thread.start()

            # let receiver run for 0.1 sec, more than timeout time
            time.sleep(0.1)

            sender_event_loop.run()

            receiver_thread.join()

            self._validate_successful_run(send_bytes, sender_node, receiver_node, sender_event_loop,
                                          receiver_event_loop)

            # verify that sender does not have any timeout triggered loops and receiver does
            self.assertEqual(sender_node.timeout_triggered_loops, 0)
            self.assertTrue(receiver_node.timeout_triggered_loops > 0)
        finally:
            if receiver_thread.is_alive():
                receiver_thread.join()

            receiver_event_loop.close()
            sender_event_loop.close()

    def test_multiplexing__delayed_connect(self):
        receiver_port = helpers.get_free_port()
        receiver_node = TestNode(receiver_port, [], 0.01)
        receiver_event_loop = create_event_loop(receiver_node)
        receiver_thread = Thread(target=receiver_event_loop.run)

        send_bytes = generate_bytearray(1000)

        sender_port = helpers.get_free_port()
        sender_node = TestNode(sender_port, [], 0.01, send_bytes)
        sender_event_loop = create_event_loop(sender_node)
        sender_thread = Thread(target=sender_event_loop.run)

        try:
            print("Starting event loop on receiver")
            receiver_thread.start()

            print("Starting event loop on sender")
            sender_thread.start()

            # let threads run for 0.1 sec
            time.sleep(0.1)

            self.assertEqual(len(receiver_node.connections), 0)
            self.assertEqual(len(sender_node.connections), 0)

            # request connection while clients are running
            sender_node.enqueue_connection('0.0.0.0', receiver_node.port)

            receiver_thread.join()
            sender_thread.join()

            self._validate_successful_run(send_bytes, sender_node, receiver_node, sender_event_loop,
                                          receiver_event_loop)
        finally:
            if receiver_thread.is_alive():
                receiver_thread.join()

            if sender_thread.is_alive():
                sender_thread.join()

            receiver_event_loop.close()
            sender_event_loop.close()

    def test_multiplexing__disconnect(self):
        receiver_port = helpers.get_free_port()
        receiver_node = TestNode(receiver_port, [], 0.01)
        receiver_event_loop = create_event_loop(receiver_node)
        receiver_thread = Thread(name="receiver", target=receiver_event_loop.run)

        sender_port = helpers.get_free_port()
        sender_node = TestNode(sender_port, [receiver_port], 0.01)
        sender_event_loop = create_event_loop(sender_node)
        sender_thread = Thread(name="sender", target=sender_event_loop.run)

        try:
            print("Starting event loop on receiver")
            receiver_thread.start()
            sender_thread.start()

            # let threads run for 0.1 sec
            time.sleep(0.1)

            self.assertEqual(len(receiver_node.connections), 1)
            self.assertEqual(len(sender_node.connections), 1)

            # request disconnect while clients are running
            sender_node.enqueue_disconnect(sender_node.connections[0][0], False)

            # sender and receiver have to disconnect and exit
            receiver_thread.join()
            sender_thread.join()
        finally:
            if receiver_thread.is_alive():
                receiver_thread.join()

            if sender_thread.is_alive():
                sender_thread.join()

            receiver_event_loop.close()
            sender_event_loop.close()

    def _validate_successful_run(self, send_bytes, sender_node, receiver_node, sender_event_loop, receiver_event_loop):
        self.assertTrue(sender_node.bytes_sent, len(send_bytes))

        self.assertTrue(len(sender_node.connections), 1)
        self.assertTrue(len(sender_event_loop._socket_connections), 1)
        self.assertEqual(sender_node.connections[0][1], '0.0.0.0')
        self.assertEqual(sender_node.connections[0][2], receiver_node.port)
        self.assertEqual(sender_node.connections[0][3], True)

        self.assertTrue(len(receiver_node.connections), 1)
        self.assertTrue(len(receiver_event_loop._socket_connections), 1)
        self.assertEqual(receiver_node.connections[0][1], '127.0.0.1')
        self.assertEqual(receiver_node.connections[0][3], False)

        bytes_received = receiver_node.receive_buffers[receiver_node.connections[0][0]]
        self.assertEqual(bytes_received, send_bytes)

        self.assertTrue(sender_node.force_exit())
        self.assertTrue(receiver_node.force_exit)
        self.assertTrue(sender_node.closed)
        self.assertTrue(receiver_node.closed)
        self.assertTrue(sender_node.initialized)
        self.assertTrue(receiver_node.initialized)
