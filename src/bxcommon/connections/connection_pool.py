from collections import defaultdict


# A group of connections with active sockets
class ConnectionPool(object):
    INITIAL_FILENO = 5000

    def __init__(self):
        self.byfileno = [None] * ConnectionPool.INITIAL_FILENO
        self.len_fileno = ConnectionPool.INITIAL_FILENO

        self.byipport = {}
        self.count_conn_by_ip = defaultdict(lambda: 0)
        self.num_peer_conn = 0

    # Add a connection for tracking.
    # Throws an AssertionError if there already exists a connection to the same
    # (ip, port) pair.
    def add(self, fileno, ip, port, conn):
        assert (ip, port) not in self.byipport

        while fileno > self.len_fileno:
            self.byfileno.extend([None] * ConnectionPool.INITIAL_FILENO)
            self.len_fileno += ConnectionPool.INITIAL_FILENO

        self.byfileno[fileno] = conn
        self.byipport[(ip, port)] = conn
        self.count_conn_by_ip[ip] += 1

    # Checks whether we have a connection to (ip, port) or not
    def has_connection(self, ip, port):
        return (ip, port) in self.byipport

    # Gets the connection by (ip, port).
    # Throws a KeyError if no such connection exists
    def get_byipport(self, ip, port):
        return self.byipport[(ip, port)]

    # Gets the connection by fileno.
    # Returns None if the fileno does not exist.
    def get_byfileno(self, fileno):
        if fileno > self.len_fileno:
            return None

        return self.byfileno[fileno]

    # Get the number of connections to this ip address.
    def get_num_conn_by_ip(self, ip):
        if ip in self.count_conn_by_ip:
            return self.count_conn_by_ip[ip]
        return 0

    # Delete this connection from the connection pool
    def delete(self, conn):
        # Remove conn from the dictionaries
        self.byfileno[conn.fileno] = None
        del self.byipport[(conn.peer_ip, conn.peer_port)]

        # Decrement the count- if it's 0, we delete the key.
        if self.count_conn_by_ip[conn.peer_ip] == 1:
            del self.count_conn_by_ip[conn.peer_ip]
        else:
            self.count_conn_by_ip[conn.peer_ip] -= 1

    # Delete this connection given its fileno.
    def delete_byfileno(self, fileno):
        return self.delete(self.byfileno[fileno])

    # Iterates through all connection objects in this connection pool
    def __iter__(self):
        for conn in self.byfileno:
            if conn is not None:
                yield conn

    # Returns the number of connections in our pool
    def __len__(self):
        return len(self.byipport)
