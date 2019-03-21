# TODO: make these integers to save us some bytes
class BloxrouteMessageType(object):
    HELLO = b"hello"
    ACK = b"ack"
    PING = b"ping"
    PONG = b"pong"
    BROADCAST = b"broadcast"
    TRANSACTION = b"tx"
    GET_TRANSACTIONS = b"gettxs"
    TRANSACTIONS = b"txs"
    KEY = b"key"
    BLOCK_HOLDING = b"blockhold"
