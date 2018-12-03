import socket
from contextlib import closing
from threading import Thread

from bxcommon.network import network_event_loop_factory


class NetworkThread(object):
    """
    Test utility class for spinning up a full node with the event loop for a longer integration test.
    """

    def __init__(self, node):
        self.node = node
        self.event_loop = network_event_loop_factory.create_event_loop(self.node)
        self._process = Thread(target=self.event_loop.run)

    def start(self):
        self._process.start()

    def close(self):
        self.node.should_force_exit = True

        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as tcp:
            try:
                tcp.connect((self.node.opts.external_ip, self.node.opts.external_port))
            except socket.error:
                pass

        if self._process.is_alive():
            self._process.join()
