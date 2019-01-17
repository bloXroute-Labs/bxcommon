from collections import defaultdict


class ConnectionPool(object):
    """
    A group of connections with active sockets.
    """
    INITIAL_FILENO = 5000

    def __init__(self):
        self.by_fileno = [None] * ConnectionPool.INITIAL_FILENO
        self.by_ipport = {}
        self.by_connection_type = defaultdict(set)
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

        while fileno > self.len_fileno:
            self.by_fileno.extend([None] * ConnectionPool.INITIAL_FILENO)
            self.len_fileno += ConnectionPool.INITIAL_FILENO

        self.by_fileno[fileno] = conn
        self.by_ipport[(ip, port)] = conn
        self.by_connection_type[conn.CONNECTION_TYPE].add(conn)
        self.count_conn_by_ip[ip] += 1

    def update_port(self, new_port, conn):
        """
        Updates port mapping of connection. Clears out old one.
        """
        old_ipport = (conn.peer_ip, conn.peer_port)
        if old_ipport in self.by_ipport:
            del self.by_ipport[old_ipport]

        self.by_ipport[(conn.peer_ip, new_port)] = conn

    def has_connection(self, ip, port):
        return (ip, port) in self.by_ipport

    def get_by_connection_type(self, connection_type):
        """
        Returns list of connections that match the connection type.
        """
        return self.by_connection_type[connection_type]

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

        self.by_connection_type[conn.CONNECTION_TYPE].discard(conn)

        # Decrement the count- if it's 0, we delete the key.
        if self.count_conn_by_ip[conn.peer_ip] == 1:
            del self.count_conn_by_ip[conn.peer_ip]
        else:
            self.count_conn_by_ip[conn.peer_ip] -= 1

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
