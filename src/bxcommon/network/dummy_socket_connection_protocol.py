from asyncio import BaseProtocol, BaseTransport, Transport
from typing import Optional, TYPE_CHECKING

import typing

from bxcommon.network.ip_endpoint import IpEndpoint
from bxutils import logging
from bxutils.logging import LogRecordType

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode

logger = logging.get_logger(__name__)
network_troubleshooting_logger = logging.get_logger(LogRecordType.NetworkTroubleshooting, __name__)


class DummySocketConnectionProtocol(BaseProtocol):
    def __init__(
        self,
        node: "AbstractNode",
        endpoint: Optional[IpEndpoint] = None,
        is_ssl: bool = True,
    ):
        pass

    def connection_made(self, transport: BaseTransport) -> None:
        transport = typing.cast(Transport, transport)
        transport.abort()
