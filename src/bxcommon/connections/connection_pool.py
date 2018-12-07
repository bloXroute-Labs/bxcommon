from collections import defaultdict


class ConnectionPool(object):
    """
    A group of connections with active sockets.
    """
    INITIAL_FILENO = 5000

    def __init__(self):
        self.byfileno = [None] * ConnectionPool.INITIAL_FILENO
        self.len_fileno = ConnectionPool.INITIAL_FILENO

        self.byipport = {}
        self.count_conn_by_ip = defaultdict(lambda: 0)
        self.num_peer_conn = 0

    def add(self, fileno, ip, port, conn):
        """
        Adds a connection for a tracking.
        Throws an AssertionError if there already exists a connection to the same (ip, port) pair.
        """
        if not isinstance(fileno, int):
            raise TypeError("Fileno is expected to be of type integer.")

        assert (ip, port) not in self.byipport

        while fileno > self.len_fileno:
            self.byfileno.extend([None] * ConnectionPool.INITIAL_FILENO)
            self.len_fileno += ConnectionPool.INITIAL_FILENO

        self.byfileno[fileno] = conn
        self.byipport[(ip, port)] = conn
        self.count_conn_by_ip[ip] += 1

    def update_port(self, new_port, conn):
        """
        Updates port mapping of connection. Clears out old one.
        """
        old_ipport = (conn.peer_ip, conn.peer_port)
        if old_ipport in self.byipport:
            del self.byipport[old_ipport]

        self.byipport[(conn.peer_ip, new_port)] = conn

    def has_connection(self, ip, port):
        return (ip, port) in self.byipport

    def get_byipport(self, ip, port):
        return self.byipport[(ip, port)]

    def get_byfileno(self, fileno):
        if fileno > self.len_fileno:
            return None
        return self.byfileno[fileno]

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
        self.byfileno[conn.fileno] = None

        # Connection might be replaced with new connection
        # Only delete from byipport if connection has the matching fileno
        connection_key = (conn.peer_ip, conn.peer_port)
        if connection_key in self.byipport and self.byipport[connection_key].fileno == conn.fileno:
            del self.byipport[(conn.peer_ip, conn.peer_port)]

        # Decrement the count- if it's 0, we delete the key.
        if self.count_conn_by_ip[conn.peer_ip] == 1:
            del self.count_conn_by_ip[conn.peer_ip]
        else:
            self.count_conn_by_ip[conn.peer_ip] -= 1

    def delete_byfileno(self, fileno):
        """
        Delete connection from connection pool via fileno.
        """
        conn = self.byfileno[fileno]
        if conn is not None:
            # noinspection PyTypeChecker
            self.delete(conn)

    def items(self):
        """
        Iterates through all of the connection objects in this connection pool.

        The pool can be freely modified while iterating here.
        """
        for fileno, conn in enumerate(self.byfileno):
            if conn is not None:
                yield fileno, conn

    def __iter__(self):
        """
        Iterates through all of the connection objects in this connection pool.

        Do not modify this pool while iterating through it here.
        """
        for ipport in self.byipport:
            yield self.byipport[ipport]

    def __len__(self):
        """
        Returns number of connections in pool.
        """
        return len(self.byipport)
