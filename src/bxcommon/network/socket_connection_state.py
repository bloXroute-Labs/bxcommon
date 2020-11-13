from bxcommon.utils.flag_enum import Flag, FlagCollection


class SocketConnectionState(Flag):
    pass


class SocketConnectionStates(FlagCollection):
    CONNECTING = SocketConnectionState()
    INITIALIZED = SocketConnectionState()
    MARK_FOR_CLOSE = SocketConnectionState()
    DO_NOT_RETRY = SocketConnectionState()
    HALT_RECEIVE = SocketConnectionState()


SocketConnectionStates.init(SocketConnectionState)
