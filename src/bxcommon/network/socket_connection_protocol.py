from asyncio import BufferedProtocol
from typing import Optional, TYPE_CHECKING

from bxcommon.network.abstract_socket_connection_protocol import AbstractSocketConnectionProtocol
from bxcommon.network.ip_endpoint import IpEndpoint
from bxutils import logging
from bxutils.logging import LogRecordType

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode

logger = logging.get_logger(__name__)
network_troubleshooting_logger = logging.get_logger(LogRecordType.NetworkTroubleshooting, __name__)


# pyre-fixme[11]: Annotation `BufferedProtocol` is not defined as a type.
class SocketConnectionProtocol(AbstractSocketConnectionProtocol, BufferedProtocol):
    def __init__(
        self,
        node: "AbstractNode",
        endpoint: Optional[IpEndpoint] = None,
        is_ssl: bool = True,
    ):
        AbstractSocketConnectionProtocol.__init__(self, node, endpoint, is_ssl)

    # pylint: disable=arguments-differ
    def get_buffer(self, _sizehint: int):
        logger.trace("[{}] - get_buffer {}.", self, _sizehint)
        return self._receive_buf

    def buffer_updated(self, nbytes: int) -> None:
        if self.is_receivable():
            logger.trace("[{}] - buffer_updated {}.", self, nbytes)
            self._node.on_bytes_received(self.file_no, self._receive_buf[:nbytes])
