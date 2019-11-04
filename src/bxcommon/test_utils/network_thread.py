import socket
from contextlib import closing
from threading import Thread

from bxutils import logging

from bxcommon.network import network_event_loop_factory

logger = logging.get_logger(__name__)


class NetworkThread(object):
    """
    Test utility class for spinning up a full node with the event loop for a longer integration test.
    """

    def __init__(self, node, name=None):
        self.node = node
        self.event_loop = network_event_loop_factory.create_event_loop(self.node)
        self._thread = Thread(target=self._run, name=name)
        self.error = None

    def start(self):
        self._thread.start()

    def close(self):
        self.node.should_force_exit = True

        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as tcp:
            try:
                tcp.connect((self.node.opts.external_ip, self.node.opts.external_port))
            except socket.error:
                pass

        if self._thread.is_alive():
            self._thread.join()

    def _run(self):
        try:
            self.event_loop.run()
        except Exception as e:
            logger.error(e)
            self.error = e

