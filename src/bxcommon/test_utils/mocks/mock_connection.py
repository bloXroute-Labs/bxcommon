from bxcommon.connections.connection_state import ConnectionState
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.buffers.output_buffer import OutputBuffer


class MockConnection(object):
    def __init__(self, fileno, address, node, from_me=False):
        self.fileno = fileno

        # (IP, Port) at time of socket creation. We may get a new application level port in
        # the version message if the connection is not from me.
        self.peer_ip, self.peer_port = address
        self.my_ip = node.server_ip
        self.my_port = node.server_port

        self.from_me = from_me  # Whether or not I initiated the connection

        self.outputbuf = OutputBuffer()
        self.inputbuf = InputBuffer()
        self.node = node

        self.is_persistent = False
        self.state = ConnectionState.CONNECTING

        # Number of bad messages I've received in a row.
        self.num_bad_messages = 0

        self.peer_desc = "%s %d" % (self.peer_ip, self.peer_port)

        self.message_handlers = None