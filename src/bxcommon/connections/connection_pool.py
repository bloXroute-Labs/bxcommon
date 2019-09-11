from collections import defaultdict, deque
from typing import List, Dict, Set, Optional, Tuple, ClassVar

from bxcommon.utils.stats import hooks
from bxcommon import constants
from bxcommon.utils import memory_utils
from bxcommon.utils import logger

from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.connection_type import ConnectionType


class ConnectionPool(object):
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

    def add(self, fileno, ip, port, conn):
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

    def index_conn_node_id(self, node_id: str, conn: AbstractConnection) -> None:
        if node_id:
            self.by_node_id[node_id].add(conn)

    def has_connection(self, ip, port):
        return (ip, port) in self.by_ipport

    def get_by_connection_type(self, connection_type: ConnectionType) -> List[AbstractConnection]:
        """
        Returns list of connections that match the connection type.
        """
        matching_types = [stored_type for stored_type in self.by_connection_type.keys() if stored_type & connection_type]
        return [connection
                for matching_type in matching_types
                for connection in self.by_connection_type[matching_type]]

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
        self.by_fileno[conn.fileno] = None

        # Connection might be replaced with new connection
        # Only delete from byipport if connection has the matching fileno
        ipport = (conn.peer_ip, conn.peer_port)
        if ipport in self.by_ipport and self.by_ipport[ipport].fileno == conn.fileno:
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

        class_name = self.__class__.__name__
        total_special_size_connection_pool = 0
        seen_ids = set()
        for conn in self.by_fileno:
            special_tuple = memory_utils.get_special_size(conn, seen_ids)
            seen_ids.update(special_tuple.seen_ids)
            total_special_size_connection_pool += special_tuple.size

        by_fileno_object_size = memory_utils.get_object_size(self.by_fileno)
        by_fileno_object_size.size += total_special_size_connection_pool

        hooks.add_obj_mem_stats(
            class_name,
            0,
            self.by_fileno,
            "connection_pool_by_fileno",
            by_fileno_object_size,
            len(self.by_fileno)
        )

        hooks.add_obj_mem_stats(
            class_name,
            0,
            self.by_ipport,
            "connection_pool_by_ipport",
            memory_utils.get_object_size(self.by_ipport),
            len(self.by_ipport)
        )

        hooks.add_obj_mem_stats(
            class_name,
            0,
            self.by_connection_type,
            "connection_pool_by_connection_type",
            memory_utils.get_object_size(self.by_connection_type),
            len(self.by_connection_type)
        )

        hooks.add_obj_mem_stats(
            class_name,
            0,
            self.count_conn_by_ip,
            "connection_pool_count_conn_by_ip",
            memory_utils.get_object_size(self.count_conn_by_ip),
            len(self.count_conn_by_ip)
        )
        self._log_connections_mem_stats()

    def _log_connections_mem_stats(self):
        for connection in self.by_ipport.values():
            hooks.reset_class_mem_stats(connection.__class__.__name__)
        for connection in self.by_ipport.values():
            connection.log_connection_mem_stats()
