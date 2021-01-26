import time

from bxcommon.connections.abstract_connection import AbstractConnection

# pylint: disable=pointless-string-statement,protected-access

"""
These are a set of testing utilities for manually instantiating an event loop to test the full
connection and send/receive cycle of a Bloxroute node.

To use, start some Bloxroute node on a background thread and create an event loop of a node in
your main thread. You can then call these functions on the event loop or node objects to simulate
the event loop without calling `event_loop.run` which runs forever.

See bxgateway/test/integration/test_gateway_connection_peering.py for an example of how to use this.
"""

# Timeout for polling on connections in integration tests
INTEGRATION_TEST_WAIT_INTERVAL_S = 1
INTEGRATION_TEST_WAIT_TIMEOUT_S = 5


# noinspection PyProtectedMember
def send_on_connection(connection):
    """
    Sends all messages on a connection's socket.
    This one will never loop infinitely; just need to flush output buffer.
    """
    connection.socket_connection.can_send = True
    while connection.outputbuf.length > 1 and connection.socket_connection.alive:
        if connection.outputbuf.last_bytearray is not None:
            connection.outputbuf.flush()
        connection.socket_connection.send()


def receive_on_connection(connection: AbstractConnection):
    """
    Receives messages on a connection's socket.
    It's not really possible to receive only one message, since this will process
    all bytes on the socket.
    """
    old_process_message = connection.process_message

    def process_message_called():
        if connection.inputbuf.length > 1:
            process_message_called.is_called = True
            old_process_message()

    # pyre-fixme[16]: Anonymous callable has no attribute `is_called`.
    process_message_called.is_called = False

    # pyre-fixme[8]: Attribute has type
    #  `BoundMethod[typing.Callable(AbstractConnection.process_message)[[Named(self,
    #  AbstractConnection[typing.Any])], typing.Any], AbstractConnection[typing.Any]]`;
    #  used as `() -> Any`.
    connection.process_message = process_message_called

    wait_while(
        lambda: not (process_message_called.is_called or not connection.is_alive()),
        # pyre-fixme[16]: `AbstractSocketConnectionProtocol` has no attribute `receive`.
        connection.socket_connection.receive
    )


# noinspection PyProtectedMember
def wait_for_a_connection(event_loop, current_connection_count):
    """
    Waits for an event loop to contain at least `current_connection_count` in its socket connection list.
    Useful for waiting for a connection request to be processed (e.g. on initialization to startup both the
    self server and send out an outgoing connection)
    """
    wait_while(
        lambda: len(event_loop._socket_connections) == current_connection_count
    )


# noinspection PyProtectedMember
def get_server_socket(event_loop):
    """
    Finds the socket connection object of the server port by excluding all the other peer ports.
    The server socket connection is the only one that does not exist in the connection pool.
    """
    ipports = event_loop._node.connection_pool.by_ipport.keys()
    outbound_filenos = [event_loop._node.connection_pool.by_ipport[ipport].fileno for ipport in ipports]
    server_initiated_connection_fileno = next(filter(lambda fileno: fileno not in outbound_filenos,
                                                     event_loop._socket_connections.keys()))
    return event_loop._socket_connections[server_initiated_connection_fileno]


# noinspection PyProtectedMember
def accept_a_connection(event_loop, server_socket):
    """
    Accepts a single connection on the event loop to the server_socket. Use when expecting the backgrounded thread
    to initiate a connection.
    """
    num_connections = len(event_loop._socket_connections)
    wait_while(
        lambda: len(event_loop._socket_connections) == num_connections,
        lambda: event_loop._handle_incoming_connections(server_socket)
    )


def _no_op_true():
    return True


def wait_while(condition=None, action=None):
    """
    Repeats action while condition is true.
    All arguments must be functions.
    """
    if condition is None:
        condition = _no_op_true
    if action is None:
        action = _no_op_true

    if not callable(condition) or not callable(action):
        raise ValueError("condition and action must be callable.")

    start_time = time.time()
    while condition():
        action()
        time.sleep(INTEGRATION_TEST_WAIT_INTERVAL_S)
        if time.time() - start_time > INTEGRATION_TEST_WAIT_TIMEOUT_S:
            raise AssertionError
