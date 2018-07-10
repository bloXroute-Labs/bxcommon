import errno
import select
import signal
import socket
from collections import defaultdict

from bxcommon.constants import MAX_CONN_BY_IP, CONNECTION_TIMEOUT, FAST_RETRY, MAX_RETRIES, RETRY_INTERVAL
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.exceptions import TerminationError
from bxcommon.utils import AlarmQueue
from bxcommon.util.logger import log_debug, log_err, log_crash, log_verbose
from bxcommon.transactions.transaction_manager import TransactionManager


class AbstractNode(object):
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.epoll = select.epoll()
        self.connection_pool = ConnectionPool()
        self.send_pings = False

        self.num_retries_by_ip = defaultdict(lambda: 0)

        # set up the server sockets for bitcoind and www/json
        self.serversocket = self.listen_on_address('0.0.0.0', self.server_port)
        self.serversocketfd = self.serversocket.fileno()
        # Handle termination gracefully
        signal.signal(signal.SIGTERM, self.kill_node)
        signal.signal(signal.SIGINT, self.kill_node)

        # Event handling queue for delayed events
        self.alarm_queue = AlarmQueue()

        self.tx_manager = TransactionManager(self)

        log_verbose("initialized node state")

    # Create and initialize a nonblocking server socket with at most 50 connections in its backlog,
    #   bound to an interface and port
    # Exit the program if there's an unrecoverable socket error (e.g. no more kernel memory)
    # Reraise the exception if it's unexpected.
    def listen_on_address(self, ip, serverport):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        log_debug("Creating a server socket on {0}:{1}".format(ip, serverport))

        try:
            s.bind((ip, serverport))
            s.listen(50)
            s.setblocking(0)
            self.epoll.register(s.fileno(), select.EPOLLIN | select.EPOLLET)
            log_debug("Finished creating a server socket on {0}:{1}".format(ip, serverport))
            return s

        except socket.error as e:
            if e.errno in [errno.EACCES, errno.EADDRINUSE, errno.EADDRNOTAVAIL, errno.ENOMEM, errno.EOPNOTSUPP]:
                log_crash("Fatal error: " + str(e.errno) + " " + e.strerror +
                          " Occurred while setting up serversocket on {0}:{1}. Exiting...".format(ip, serverport))
                exit(1)
            else:
                log_crash("Fatal error: " + str(e.errno) + " " + e.strerror +
                          " Occurred while setting up serversocket on {0}:{1}. Reraising".format(ip, serverport))
                raise e

    # Make a new conn_cls instance who is connected to (ip, port) and schedule connection_timeout to check its status.
    # If setup is False, then sock is an already established socket. Otherwise, we must initialize and set up socket.
    # If trusted is True, the instance should be marked as a trusted connection.
    def connect_to_address(self, conn_cls, ip, port, sock=None, setup=False):
        log_debug("Initiating connection to {0}:{1}.".format(ip, port))

        # If we're already connected to the remote peer, log the event and ignore it.
        if self.connection_pool.has_connection(ip, port):
            log_err("Connection to {0}:{1} already exists!".format(ip, port))
            if sock is not None:
                try:
                    sock.close()
                except socket.error:
                    pass

            return

        initialized = True  # True if socket is connected. False otherwise.

        # Create a socket and connect to (ip, port).
        if setup:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.setblocking(0)
                sock.connect((ip, port))
            except socket.error as e:
                if e.errno in [errno.EPERM, errno.EADDRINUSE]:
                    log_err("Connection to {0}:{1} failed! Got errno {2} with msg {3}."
                            .format(ip, port, e.errno, e.strerror))
                    return
                elif e.errno in [errno.EAGAIN, errno.ECONNREFUSED, errno.EINTR, errno.EISCONN, errno.ENETUNREACH,
                                 errno.ETIMEDOUT]:
                    raise RuntimeError('FIXME')

                    # FIXME conn_obj and trusted are not defined, delete trust, alarm register call and test
                    # log_err("Node.connect_to_address",
                    #         "Connection to {0}:{1} failed. Got errno {2} with msg {3}. Retry?: {4}"
                    #         .format(ip, port, e.errno, e.strerror, conn_obj.trusted))
                    # if trusted:
                    #     self.alarm_queue.register_alarm(FAST_RETRY, self.retry_init_client_socket, sock, conn_cls, ip,
                    #                                     port, setup)
                    # return
                elif e.errno in [errno.EALREADY]:
                    # Can never happen because this thread is the only one using the socket.
                    log_err("Got EALREADY while connecting to {0}:{1}.".format(ip, port))
                    exit(1)
                elif e.errno in [errno.EINPROGRESS]:
                    log_debug("Got EINPROGRESS on {0}:{1}. Will wait for ready outputbuf.".format(ip, port))
                    initialized = False
                else:
                    raise e
        else:
            # Even if we didn't set up this socket, we still need to make it nonblocking.
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setblocking(0)

        # Make a connection object and set its state
        conn_obj = conn_cls(sock, (ip, port), self, setup=setup, from_me=setup)
        conn_obj.state |= ConnectionState.CONNECTING if initialized else ConnectionState.INITIALIZED

        self.alarm_queue.register_alarm(CONNECTION_TIMEOUT, self.connection_timeout, conn_obj)

        # Make the connection object publicly accessible
        self.connection_pool.add(sock.fileno(), ip, port, conn_obj)
        self.epoll.register(sock.fileno(),
                            select.EPOLLOUT | select.EPOLLIN | select.EPOLLERR | select.EPOLLHUP | select.EPOLLET)

        log_debug("Connected {0}:{1} on file descriptor {2} with state {3}"
                  .format(ip, port, sock.fileno(), conn_obj.state))
        return

    # Handles incoming connections on the server socket
    # Only allows MAX_CONN_BY_IP connections from each IP address to be initialized.
    def handle_incoming_connections(self):
        log_verbose("new connection establishment starting")
        try:
            while True:
                new_socket, address = self.serversocket.accept()
                log_debug("new connection from {0}".format(address))
                ip = address[0]

                # If we have too many connections, then we close this new socket and move on.
                if self.connection_pool.get_num_conn_by_ip(ip) >= MAX_CONN_BY_IP:
                    log_err("The IP {0} has too many connections! Closing...".format(ip))
                    new_socket.close()
                else:
                    log_debug("Establishing connection number {0} from {1}"
                              .format(self.connection_pool.get_num_conn_by_ip(ip), ip))
                    # The trusted bit here will be set when we get the application layer address.
                    conn_cls = self.get_connection_class(ip)
                    self.connect_to_address(conn_cls, address[0], address[1], new_socket, setup=False)

        except socket.error:
            pass

    # Broadcasts message msg to every connection except requester.
    def broadcast(self, msg, broadcasting_conn):
        if broadcasting_conn is not None:
            log_debug("Broadcasting message to everyone from {0}".format(broadcasting_conn.peer_desc))
        else:
            log_debug("Broadcasting message to everyone")

        for conn in self.connection_pool:
            if conn.state & ConnectionState.ESTABLISHED and conn != broadcasting_conn:
                conn.enqueue_msg(msg)

    # Cleans up system resources used by this node.
    def cleanup_node(self):
        log_err("Node is closing! Closing everything.")

        # Clean up server sockets.
        self.epoll.unregister(self.serversocket.fileno())
        self.serversocket.close()

        # Clean up client sockets.
        for conn in self.connection_pool:
            self.destroy_conn(conn.fileno, teardown=True)

        self.epoll.close()

    # Kills the node immediately
    def kill_node(self, _signum, _stack):
        raise TerminationError("Node killed.")

    # Clean up the associated connection and update all data structures tracking it.
    # We also retry trusted connections since they can never be destroyed.
    # If teardown is True, then we do not retry trusted connections and just tear everything down.
    def destroy_conn(self, fileno, teardown=False):
        conn = self.connection_pool.get_byfileno(fileno)
        log_debug("Breaking connection to {0}".format(conn.peer_desc))

        # Get rid of the connection from the epoll and the connection pool.
        self.epoll.unregister(fileno)
        self.connection_pool.delete(conn)

        conn.close()

        if self.can_retry_after_destroy(teardown, conn):
            log_debug("Retrying connection to {0}".format(conn.peer_desc))
            self.alarm_queue.register_alarm(
                FAST_RETRY, self.retry_init_client_socket, None,
                conn.__class__, conn.peer_ip, conn.peer_port, True)

    # Check if the connection is established.
    # If it is not established, we give up for untrusted connections and try again for trusted connections.
    def connection_timeout(self, conn):
        log_debug("Connection timeout, on connection with {0}".format(conn.peer_desc))

        if conn.state & ConnectionState.ESTABLISHED:
            log_debug("Turns out connection was initialized, carrying on with {0}".format(conn.peer_desc))
            self.alarm_queue.register_alarm(60, conn.send_ping)
            return 0

        if conn.state & ConnectionState.MARK_FOR_CLOSE:
            log_debug("We're already closing the connection to {0} (or have closed it). Ignoring timeout."
                      .format(conn.peer_desc))
            return 0

        # Clean up the old connection and retry it if it is trusted
        log_debug("destroying old socket with {0}".format(conn.peer_desc))
        self.destroy_conn(conn.sock.fileno())

        # It is connect_to_address's job to schedule this function.
        return 0

    # Retrys the connect_to_address call
    # Returns 0 to be allowed as a function for the AlarmQueue and not be rescheduled
    def retry_init_client_socket(self, sock, conn_cls, ip, port, setup):
        self.num_retries_by_ip[ip] += 1
        if self.num_retries_by_ip[ip] >= MAX_RETRIES:
            del self.num_retries_by_ip[ip]
            log_debug("Not retrying connection to {0}:{1}- maximum connections exceeded!".format(ip, port))
            return 0
        else:
            log_debug("Retrying connection to {0}:{1}.".format(ip, port))
            self.connect_to_address(conn_cls, ip, port, sock, setup)
        return 0

    # Main loop of this Node. Returns when Node crashes or is stopped.
    # Handles events as they get triggered by epoll.
    # Fires alarms that get scheduled.
    def run(self):
        self.connect_to_peers()

        try:
            _, timeout = self.alarm_queue.time_to_next_alarm()
            while True:
                # Grab all events.
                try:
                    events = self.epoll.poll(timeout)
                except IOError as ioe:
                    if ioe.errno == errno.EINTR:
                        log_verbose("got interrupted in epoll")
                        continue
                    raise ioe

                for fileno, event in events:
                    conn = self.connection_pool.get_byfileno(fileno)

                    if conn is not None:
                        # Mark this connection for close if we received a POLLHUP. No other functions will be called
                        #   on this connection.
                        if event & select.EPOLLHUP:
                            conn.state |= ConnectionState.MARK_FOR_CLOSE

                        if event & select.EPOLLOUT and not conn.state & ConnectionState.MARK_FOR_CLOSE:
                            # If connect received EINPROGRESS, we will receive an EPOLLOUT if connect succeeded
                            if not conn.state & ConnectionState.INITIALIZED:
                                conn.state = conn.state | ConnectionState.INITIALIZED

                            # Mark the connection as sendable and send as much as we can from the outputbuffer.
                            conn.mark_sendable()
                            conn.send()

                    # handle incoming connection on the server port
                    elif fileno == self.serversocketfd:
                        self.handle_incoming_connections()

                    else:
                        assert False, "Connection not handled!"

                # Handle EPOLLIN events.
                for fileno, event in events:
                    # we already handled the new connections above, no need to handle them again
                    if fileno != self.serversocketfd:
                        conn = self.connection_pool.get_byfileno(fileno)

                        if event & select.EPOLLIN and not conn.state & ConnectionState.MARK_FOR_CLOSE:
                            # log_debug("Node.run", "recv event on {0}".format(conn.peer_desc))
                            conn.recv()

                        # Done processing. Close socket if it got put on the blacklist or was marked for close.
                        if conn.state & ConnectionState.MARK_FOR_CLOSE:
                            log_debug("Connection to {0} closing".format(conn.peer_desc))
                            self.destroy_conn(fileno)
                            if conn.is_persistent:
                                self.alarm_queue.register_alarm(RETRY_INTERVAL, self.retry_init_client_socket, None,
                                                                conn.__class__, conn.peer_ip, conn.peer_port, True)

                timeout = self.alarm_queue.fire_ready_alarms(not events)

        # Handle shutdown of this node.
        finally:
            self.cleanup_node()

    def can_retry_after_destroy(self, teardown, conn):
        raise NotImplementedError()

    def get_connection_class(self, ip=None):
        raise NotImplementedError()

    def connect_to_peers(self):
        raise NotImplementedError()
