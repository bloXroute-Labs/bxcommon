from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Optional, List, Iterable, TypeVar, Generic

from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.messages.abstract_message import AbstractMessage
from bxutils import logging

MT = TypeVar("MT", bound=AbstractMessage)
CT = TypeVar("CT", bound=AbstractConnection)
logger = logging.get_logger(__name__)


@dataclass
class BroadcastOptions:
    broadcasting_connection: Optional[AbstractConnection] = None
    prepend_to_queue: bool = False
    connection_types: Iterable[ConnectionType] = field(default_factory=list)


class BroadcastService(Generic[MT, CT], ABC):
    connection_pool: ConnectionPool

    def __init__(self, connection_pool: ConnectionPool) -> None:
        self.connection_pool = connection_pool

    def broadcast(self, message: MT, options: BroadcastOptions) -> List[CT]:
        if options.broadcasting_connection is not None:
            logger.log(message.log_level(), "Broadcasting {} to [{}] connections from {}.",
                       message, ",".join(map(str, options.connection_types)), options.broadcasting_connection)
        else:
            logger.log(message.log_level(), "Broadcasting {} to [{}] connections.", message,
                       ",".join(map(str, options.connection_types)))

        connections = self.get_connections_for_broadcast(message, options)
        return self.broadcast_to_connections(message, connections, options)

    @abstractmethod
    def should_broadcast_to_connection(self, message: MT, connection: CT) -> bool:
        pass

    def get_connections_for_broadcast(self, message: MT, options: BroadcastOptions) -> List[CT]:
        connections = []
        # pyre-fixme[6]: Expected `List[ConnectionType]` for 1st param but got `Iterable[ConnectionType]`.
        for connection in self.connection_pool.get_by_connection_types(options.connection_types):
            if (
                self.should_broadcast_to_connection(message, connection) and
                connection != options.broadcasting_connection
            ):
                connections.append(connection)
        return connections

    def broadcast_to_connections(
        self, message: AbstractMessage, connections: Iterable[CT], options: BroadcastOptions
    ) -> List[CT]:
        broadcast_connections = []
        for connection in connections:
            if connection.is_active():
                connection.enqueue_msg(message, options.prepend_to_queue)
                broadcast_connections.append(connection)
        return broadcast_connections
