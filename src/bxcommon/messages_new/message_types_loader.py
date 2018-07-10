_msg_types = None


# FIXME refactor the circular parent-child-parent dependencies in messages
# Messages depends on this type dict which depends on Messages
#   Suggest changing the messages impl to be a factory pattern
def get_message_types():
    global _msg_types

    if _msg_types:
        return _msg_types

    from bxcommon.messages_new.ack_message import AckMessage
    from bxcommon.messages_new.broadcast_message import BroadcastMessage
    from bxcommon.messages_new.hello_message import HelloMessage
    from bxcommon.messages_new.ping_message import PingMessage
    from bxcommon.messages_new.pong_message import PongMessage
    from bxcommon.messages_new.tx_assign_message import TxAssignMessage
    from bxcommon.messages_new.tx_message import TxMessage

    _msg_types = {
        'hello': HelloMessage,
        'ack': AckMessage,
        'ping': PingMessage,
        'pong': PongMessage,
        'broadcast': BroadcastMessage,
        'tx': TxMessage,
        'txassign': TxAssignMessage,
    }

    return _msg_types
