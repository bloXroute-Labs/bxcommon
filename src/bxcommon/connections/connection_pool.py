from collections import defaultdict
from typing import Iterable
from typing import List, Dict, Set, Optional, Tuple, ClassVar
import time
from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.utils import memory_utils
from bxcommon.utils.stats.memory_statistics_service import memory_statistics
from bxcommon.utils.stats import hooks
from bxutils import logging

logger = logging.get_logger(__name__)


class ConnectionPool:
    """
    A group of connections with active sockets.
    """
    INITIAL_FILENO: ClassVar[int] = 100

    by_fileno: List[Optional[AbstractConnection]]
    by_ipport: Dict[Tuple[str, int], AbstractConnection]
    by_connection_type: Dict[ConnectionType, Set[AbstractConnection]]
    by_node_id: Dict[str, Set[AbstractConnection]]
    len_fileno: int
    count_conn_by_ip: Dict[str, int]
    num_peer_conn: int

    def __init__(self):
        self.by_fileno = [None] * ConnectionPool.INITIAL_FILENO
        self.by_ipport = {}
        self.by_connection_type = defaultdict(set)
        self.by_node_id = defaultdict(set)
        self.len_fileno = ConnectionPool.INITIAL_FILENO
        self.count_conn_by_ip = defaultdict(lambda: 0)
        self.num_peer_conn = 0

    def add(self, fileno: int, ip: str, port: int, conn: AbstractConnection):
        """
        Adds a connection for a tracking.
        Throws an AssertionError if there already exists a connection to the same (ip, port) pair.
        """
        if not isinstance(fileno, int):
            raise TypeError("Fileno is expected to be of type integer.")

        assert (ip, port) not in self.by_ipport

        while fileno >= self.len_fileno:
            self.by_fileno.extend([None] * ConnectionPool.INITIAL_FILENO)
            self.len_fileno += ConnectionPool.INITIAL_FILENO

        self.by_fileno[fileno] = conn
        self.by_ipport[(ip, port)] = conn
        self.by_connection_type[conn.CONNECTION_TYPE].add(conn)
        self.count_conn_by_ip[ip] += 1

    def update_port(self, old_port, new_port, conn):
        """
        Updates port mapping of connection. Clears out old one.
        """
        old_ipport = (conn.peer_ip, old_port)
        if old_ipport in self.by_ipport:
            del self.by_ipport[old_ipport]

        self.by_ipport[(conn.peer_ip, new_port)] = conn

    def update_connection_type(self, conn: AbstractConnection, connection_type: ConnectionType):
        self.delete(conn)
        conn.CONNECTION_TYPE = connection_type
        self.add(conn.file_no, conn.peer_ip, conn.peer_port, conn)
        self.index_conn_node_id(conn.peer_id, conn)

    def index_conn_node_id(self, node_id: str, conn: AbstractConnection) -> None:
        if node_id:
            self.by_node_id[node_id].add(conn)

    def has_connection(self, ip, port):
        return (ip, port) in self.by_ipport

    def get_by_connection_type(self, connection_type: ConnectionType) -> Set[AbstractConnection]:
        """
        Returns list of connections that match the connection type.
        """
        return self.get_by_connection_types({connection_type})

    def get_by_connection_types(self, connection_types: Iterable[ConnectionType]) -> Set[AbstractConnection]:
        matching_types = [stored_type for stored_type in self.by_connection_type.keys() if
                          any(stored_type & connection_type for connection_type in connection_types)]
        return {connection
                for matching_type in matching_types
                for connection in self.by_connection_type[matching_type]}

    def get_by_ipport(self, ip, port):
        return self.by_ipport[(ip, port)]

    def get_by_fileno(self, fileno):
        if fileno > self.len_fileno:
            return None
        return self.by_fileno[fileno]

    def get_num_conn_by_ip(self, ip):
        """
        Gets the number of connections to this IP address.
        """
        if ip in self.count_conn_by_ip:
            return self.count_conn_by_ip[ip]
        return 0

    def get_by_node_id(self, node_id: str) -> Set[AbstractConnection]:
        """
        Returns list of connections where the peer_id matches the node id param

        NOTE: The connection's peer_id attribute only gets assigned once the hello message is received so you will only
        be able to retrieve connections by node id once this has been exchanged

        :param node_id: node id to match
        :return: list of matched connections
        """
        return self.by_node_id[node_id]

    def delete(self, conn):
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

        for connection_type in self.by_connection_type:
            if connection_type & conn.CONNECTION_TYPE:
                self.by_connection_type[connection_type].discard(conn)

        # Decrement the count- if it's 0, we delete the key.
        if self.count_conn_by_ip[conn.peer_ip] == 1:
            del self.count_conn_by_ip[conn.peer_ip]
        else:
            self.count_conn_by_ip[conn.peer_ip] -= 1

        if conn.peer_id and conn.peer_id in self.by_node_id:
            if len(self.get_by_node_id(conn.peer_id)) == 1:
                del self.by_node_id[conn.peer_id]
            else:
                self.by_node_id[conn.peer_id].discard(conn)

    def delete_by_fileno(self, fileno):
        """
        Delete connection from connection pool via fileno.
        """
        conn = self.by_fileno[fileno]
        if conn is not None:
            # noinspection PyTypeChecker
            self.delete(conn)

    def items(self):
        """
        Iterates through all of the connection objects in this connection pool.

        The pool can be freely modified while iterating here.
        """
        for fileno, conn in enumerate(self.by_fileno):
            if conn is not None:
                yield fileno, conn

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
