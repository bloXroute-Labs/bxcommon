from enum import IntFlag


class ConnectionState(IntFlag):
    CONNECTING = 0
    INITIALIZED = 1
    HELLO_RECVD = 2
    HELLO_ACKD = 4
    ESTABLISHED = INITIALIZED | HELLO_RECVD | HELLO_ACKD

    def __str__(self):
        return self.name
