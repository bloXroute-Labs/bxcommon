from enum import Flag, auto


class SocketConnectionState(Flag):
    CONNECTING = auto()
    INITIALIZED = auto()
    MARK_FOR_CLOSE = auto()
