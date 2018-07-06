class ConnectionState(object):
    CONNECTING = 0b000000000  # Received EINPROGRESS when calling socket.connect
    INITIALIZED = 0b000000001
    HELLO_RECVD = 0b000000010  # Received version message from the remote end
    HELLO_ACKD = 0b000000100  # Received verack message from the remote end
    ESTABLISHED = 0b000000111  # Received version + verack message, is initialized
    MARK_FOR_CLOSE = 0b001000000  # Connection is closed