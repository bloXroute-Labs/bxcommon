import errno
import hashlib
import select
import socket

from enum import Enum

from bxcommon.utils import *

MAX_CONN_BY_IP = 30  # Maximum number of connections that an IP address can have

CONNECTION_TIMEOUT = 30  # Number of seconds that we wait to retry a connection.
FAST_RETRY = 3  # Seconds before we retry in case of transient failure (e.g. EINTR thrown)
MAX_RETRIES = 10

# Number of bad messages I'm willing to receive in a row before declaring the input stream
# corrupt beyond repair.
MAX_BAD_MESSAGES = 3

# The size of the recv buffer that we fill each time.
RECV_BUFSIZE = 8192

RETRY_INTERVAL = 30  # Seconds before we retry in case of orderly shutdown

sha256 = hashlib.sha256

MAX_WAIT_TIME = 60  # Seconds timeout for the sink

# Number of messages that can be cut through at a time
MAX_SEND_QUEUE_SIZE = 5000

# Number of messages that can be kept in the history at a time.
# Two identical messages that are broadcast more than MAX_MESSAGE_HISTORY messages apart
# will both be cut through broadcast.
MAX_MESSAGE_HISTORY = 5000


class AbstractClient(object):

    # Create and initialize a nonblocking server socket with at most 50 connections in its backlog,
    #   bound to an interface and port
    # Exit the program if there's an unrecoverable socket error (e.g. no more kernel memory)
    # Reraise the exception if it's unexpected.
    def create_server_socket(self, intf, serverport):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        log_debug("Creating a server socket on {0}:{1}".format(intf, serverport))

        try:
            s.bind((intf, serverport))
            s.listen(50)
            s.setblocking(0)
            self.epoll.register(s.fileno(), select.EPOLLIN | select.EPOLLET)
            log_debug("Finished creating a server socket on {0}:{1}".format(intf, serverport))
            return s

        except socket.error as e:
            if e.errno in [errno.EACCES, errno.EADDRINUSE, errno.EADDRNOTAVAIL, errno.ENOMEM, errno.EOPNOTSUPP]:
                log_crash("Fatal error: " + str(e.errno) + " " + e.strerror +
                          " Occurred while setting up serversocket on {0}:{1}. Exiting...".format(intf, serverport))
                exit(1)
            else:
                log_crash("Fatal error: " + str(e.errno) + " " + e.strerror +
                          " Occurred while setting up serversocket on {0}:{1}. Reraising".format(intf, serverport))
                raise e

    # Make a new conn_cls instance who is connected to (ip, port) and schedule connection_timeout to check its status.
    # If setup is False, then sock is an already established socket. Otherwise, we must initialize and set up socket.
    # If trusted is True, the instance should be marked as a trusted connection.
    def init_client_socket(self, conn_cls, ip, port, sock=None, setup=False):
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
                    # log_err("Node.init_client_socket",
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


class ConnectionState():
    CONNECTING = 0b000000000  # Received EINPROGRESS when calling socket.connect
    INITIALIZED = 0b000000001
    HELLO_RECVD = 0b000000010  # Received version message from the remote end
    HELLO_ACKD = 0b000000100  # Received verack message from the remote end
    ESTABLISHED = 0b000000111  # Received version + verack message, is initialized
    MARK_FOR_CLOSE = 0b001000000  # Connection is closed
