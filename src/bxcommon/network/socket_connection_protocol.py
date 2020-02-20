import time
from asyncio import BufferedProtocol
from typing import Optional

from bxcommon import constants
from bxcommon.network.abstract_socket_connection_protocol import AbstractSocketConnectionProtocol
from bxcommon.network.ip_endpoint import IpEndpoint
from bxcommon.utils import performance_utils
from bxutils import logging
from bxutils.logging import LogRecordType

network_troubleshooting_logger = logging.get_logger(LogRecordType.NetworkTroubleshooting, __name__)


class SocketConnectionProtocol(AbstractSocketConnectionProtocol, BufferedProtocol):
    def __init__(
        self,
        node: "AbstractNode",
        endpoint: Optional[IpEndpoint] = None,
        is_ssl: bool = True,
    ):
        AbstractSocketConnectionProtocol.__init__(self, node, endpoint, is_ssl)

        self._receive_buf = bytearray(constants.RECV_BUFSIZE)
        self._read_start_time = None

    def get_buffer(self, _suggested_size: int):
        self._read_start_time = time.time()
        return self._receive_buf

    def buffer_updated(self, bytes_len: int):
        assert self._read_start_time is not None
        performance_utils.log_operation_duration(network_troubleshooting_logger,
                                                 "Read bytes", self._read_start_time,
                                                 constants.NETWORK_OPERATION_CYCLE_DURATION_WARN_THRESHOLD_S,
                                                 connection=self, bytes_len=bytes_len)

        if self.is_receivable():
            self._node.on_bytes_received(self.file_no, self._receive_buf[:bytes_len])
