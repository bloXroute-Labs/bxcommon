import functools
from collections import defaultdict
from itertools import chain
from typing import Iterable
from typing import List, Dict, Optional, Tuple, ClassVar
import time
from more_itertools import flatten

from prometheus_client import Gauge

from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.utils import memory_utils
from bxcommon.utils.stats import hooks
from bxcommon.utils.stats.memory_statistics_service import memory_statistics
from bxutils import logging

logger = logging.get_logger(__name__)


class ConnectionPool:
    """
    Class for managing a set of connection handlers over a node's lifecycle.

    Connections should be thought of unique identified by via file no or node id.
    (ip, port) will sometimes be used for look ups, but can sometimes be unreliable to identify
    a connection to another node depending on who initiates the connection.

    Try to avoid writing code that needs to rely on looking up connections by (ip, port), and
    include fallbacks for node id lookup.

    Lookups without node id are still allowed to support preSSL connections that
    do not have as strong guarantees on identifying connections by node id.
    """
    INITIAL_FILENO: ClassVar[int] = 100

    by_ipport: Dict[Tuple[str, int], AbstractConnection]
    by_connection_type: Dict[ConnectionType, List[AbstractConnection]]
    by_node_id: Dict[str, AbstractConnection]
    len_fileno: int
    count_conn_by_ip: Dict[str, int]

    def __init__(self) -> None:
        self.by_fileno = [None] * ConnectionPool.INITIAL_FILENO
        self.by_ipport = {}
        self.by_connection_type = defaultdict(list)
        self.by_node_id = {}
        self.len_fileno = ConnectionPool.INITIAL_FILENO
        self.count_conn_by_ip = defaultdict(lambda: 0)

        self._create_metrics()

    def add(self, fileno: int, ip: str, port: int, conn: AbstractConnection) -> None:
        """
        Adds a connection for a tracking.
        Throws an AssertionError if there already exists a connection to the same (ip, port) pair.
        """
        assert (ip, port) not in self.by_ipport

        while fileno >= self.len_fileno:
            self.by_fileno.extend([None] * ConnectionPool.INITIAL_FILENO)
            self.len_fileno += ConnectionPool.INITIAL_FILENO

        self.by_fileno[fileno] = conn
        self.by_ipport[(ip, port)] = conn
        self.by_connection_type[conn.CONNECTION_TYPE].append(conn)
        self.count_conn_by_ip[ip] += 1

    def update_port(self, old_port: int, new_port: int, conn: AbstractConnection) -> None:
        """
        Updates port mapping of connection. Clears out old one.
        """
        old_ipport = (conn.peer_ip, old_port)
        if old_ipport in self.by_ipport:
            del self.by_ipport[old_ipport]

        self.by_ipport[(conn.peer_ip, new_port)] = conn

    def update_connection_type(self, conn: AbstractConnection, connection_type: ConnectionType) -> None:
        self.delete(conn)

        # pyre-ignore this is how we currently identify connections
        conn.CONNECTION_TYPE = connection_type
        conn.format_connection()
        self.add(conn.file_no, conn.peer_ip, conn.peer_port, conn)

        peer_id = conn.peer_id
        assert peer_id is not None
        self.index_conn_node_id(peer_id, conn)

    def index_conn_node_id(self, node_id: str, conn: AbstractConnection) -> None:
        self.by_node_id[node_id] = conn

    def has_connection(
            self, ip: Optional[str] = None, port: Optional[int] = None, node_id: Optional[str] = None) -> bool:
        if node_id is not None and node_id in self.by_node_id:
            return True
        if ip is None or port is None:
            return False
        return (ip, port) in self.by_ipport

    def get_connection_by_network_num(self, network_num: int) -> Iterable[AbstractConnection]:
        for connection in self.get_by_connection_types(
            (ConnectionType.GATEWAY, ConnectionType.RELAY_PROXY)
        ):
            if connection.network_num == network_num:
                yield connection

    def get_by_connection_types(
        self, connection_types: Tuple[ConnectionType, ...]
    ) -> List[AbstractConnection]:
        # pyre-fixme [7]: Expected `List[AbstractConnection[typing.Any]]`
        #  but got `typing.Iterator[Variable[more_itertools.recipes._T]]`.
        return flatten(self._iter_by_connection_types(connection_types))

    def _iter_by_connection_types(
        self, connection_types: Tuple[ConnectionType, ...]
    ) -> Iterable[AbstractConnection]:
        for connection_type, connections in self.by_connection_type.items():
            if any(connection_type & matching_type for matching_type in connection_types):
                # pyre-fixme[7]: Expected `Iterable[AbstractConnection[typing.Any]]`
                #  but got `typing.Generator[chain[AbstractConnection[typing.Any]], None, None]`.
                yield chain(connections)

    def get_by_ipport(self, ip: str, port: int, node_id: Optional[str] = None) -> AbstractConnection:
        ip_port = (ip, port)
        if ip_port in self.by_ipport:
            return self.by_ipport[ip_port]

        if node_id is not None and node_id in self.by_node_id:
            return self.by_node_id[node_id]

        raise KeyError(f"Could not find a connection with ip port: {ip_port} or node id: {node_id}")

    def get_by_fileno(self, fileno: int) -> Optional[AbstractConnection]:
        if fileno >= self.len_fileno:
            return None
        return self.by_fileno[fileno]

    def get_by_node_id(self, node_id: str) -> AbstractConnection:
        return self.by_node_id[node_id]

    def delete(self, conn: AbstractConnection) -> None:
        """
        Delete connection from connection pool.
        """
        # Remove conn from the dictionaries
        self.by_fileno[conn.file_no] = None

        # Connection might be replaced with new connection
        # Only delete from byipport if connection has the matching fileno
        ipport = (conn.peer_ip, conn.peer_port)
        if ipport in self.by_ipport and self.by_ipport[ipport].file_no == conn.file_no:
            del self.by_ipport[(conn.peer_ip, conn.peer_port)]

        if conn.CONNECTION_TYPE in self.by_connection_type:
            if len(self.by_connection_type[conn.CONNECTION_TYPE]) == 1:
                del self.by_connection_type[conn.CONNECTION_TYPE]
            else:
                self.by_connection_type[conn.CONNECTION_TYPE].remove(conn)

        # Decrement the count- if it's 0, we delete the key.
        if self.count_conn_by_ip[conn.peer_ip] == 1:
            del self.count_conn_by_ip[conn.peer_ip]
        else:
            self.count_conn_by_ip[conn.peer_ip] -= 1

        peer_id = conn.peer_id
        if peer_id and peer_id in self.by_node_id:
            del self.by_node_id[peer_id]

    def items(self):
        """
        Iterates through all of the connection objects in this connection pool.

        The pool can be freely modified while iterating here.
        """
        for fileno, conn in enumerate(self.by_fileno):
            if conn is not None:
                yield fileno, conn

    def __repr__(self) -> str:
        return repr(list(self.by_ipport.values()))

    def __iter__(self):
        """
        Iterates through all of the connection objects in this connection pool.

        Do not modify this pool while iterating through it here.
        """
        for ipport in self.by_ipport:
            yield self.by_ipport[ipport]

    def __len__(self):
        """
        Returns number of connections in pool.
        """
        return len(self.by_ipport)

    def log_connection_pool_mem_stats(self):
        """
        Logs Connection Pool memory statistics
        """

        sizer_obj = memory_statistics.sizer_obj
        sizer = sizer_obj.sizer
        logger.trace("MemoryStats excluded classes: {}", sizer_obj.excluded)

        by_fileno_obj_size = self._log_detailed_object_size(self.by_fileno, "by_fileno", sizer=sizer)
        by_ipport_obj_size = self._log_detailed_object_size(self.by_ipport, "by_ipport", sizer=sizer)
        by_conn_type_obj_size = self._log_detailed_object_size(self.by_connection_type, "by_conn_type", sizer=sizer)
        by_node_id_obj_size = self._log_detailed_object_size(self.by_node_id, "by_node_id", sizer=sizer)

        class_name = self.__class__.__name__
        hooks.add_obj_mem_stats(
            class_name,
            0,
            self.by_fileno,
            "connection_pool_by_fileno",
            by_fileno_obj_size,
            object_item_count=sum([1 for i in self.by_fileno if i is not None]),
            object_type=memory_utils.ObjectType.META,
            size_type=memory_utils.SizeType.OBJECT
        )

        hooks.add_obj_mem_stats(
            class_name,
            0,
            self.by_ipport,
            "connection_pool_by_ipport",
            by_ipport_obj_size,
            object_item_count=len(self.by_ipport),
            object_type=memory_utils.ObjectType.META,
            size_type=memory_utils.SizeType.OBJECT
        )

        hooks.add_obj_mem_stats(
            class_name,
            0,
            self.by_node_id,
            "connection_pool_by_node_id",
            by_node_id_obj_size,
            object_item_count=len(self.by_node_id),
            object_type=memory_utils.ObjectType.META,
            size_type=memory_utils.SizeType.OBJECT
        )

        hooks.add_obj_mem_stats(
            class_name,
            0,
            self.by_connection_type,
            "connection_pool_by_connection_type",
            by_conn_type_obj_size,
            object_item_count=len(self.by_connection_type),
            object_type=memory_utils.ObjectType.META,
            size_type=memory_utils.SizeType.OBJECT
        )

        hooks.add_obj_mem_stats(
            class_name,
            0,
            self.count_conn_by_ip,
            "connection_pool_count_conn_by_ip",
            memory_utils.get_object_size(self.count_conn_by_ip),
            object_item_count=len(self.count_conn_by_ip),
            object_type=memory_utils.ObjectType.BASE,
            size_type=memory_utils.SizeType.TRUE
        )
        self._log_connections_mem_stats()

    def _log_detailed_object_size(self, obj, stat_name, sizer):
        class_name = self.__class__.__name__
        start_time = time.time()
        obj_size = memory_utils.get_detailed_object_size(obj, sizer=sizer)
        logger.debug("(MemoryStats) ({}) {} took: {:.3f} seconds", class_name, stat_name, time.time() - start_time)
        return obj_size

    def _log_connections_mem_stats(self):
        by_fileno_size = len(self.by_fileno)
        for conn_index in range(by_fileno_size):
            conn = self.by_fileno[conn_index]
            if conn is not None:
                hooks.reset_class_mem_stats(conn.__class__.__name__)

        for conn_index in range(by_fileno_size):
            conn = self.by_fileno[conn_index]
            if conn is not None:
                conn.log_connection_mem_stats()

    # Not used right now but is helpful for debugging
    def _get_ref_info(self, parent_obj):
        return [(obj.name, obj.size, self._get_ref_info(obj)) for obj in parent_obj.references]

    def _create_metrics(self) -> None:
        self.connections_gauge = Gauge(
            "peer_count",
            "Number of peers node is connected to",
            ("connection_type",)
        )
        self.connections_gauge.labels("total").set_function(
            functools.partial(len, self.by_ipport)
        )
        self.connections_gauge.labels("blockchain").set_function(
            functools.partial(self._get_number_of_connections, ConnectionType.BLOCKCHAIN_NODE)
        )
        self.connections_gauge.labels("relay_transaction").set_function(
            functools.partial(self._get_number_of_connections, ConnectionType.RELAY_TRANSACTION)
        )
        self.connections_gauge.labels("relay_block").set_function(
            functools.partial(self._get_number_of_connections, ConnectionType.RELAY_BLOCK)
        )
        self.connections_gauge.labels("relay_all").set_function(
            functools.partial(self._get_number_of_connections, ConnectionType.RELAY_ALL)
        )

    def _get_number_of_connections(self, connection_type: ConnectionType) -> int:
        return len(list(self.get_by_connection_types((connection_type,))))
