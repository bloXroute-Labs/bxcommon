# TODO: make these integers to save us some bytes
class BloxrouteMessageType(object):
    HELLO = "hello"
    ACK = "ack"
    PING = "ping"
    PONG = "pong"
    BROADCAST = "broadcast"
    TRANSACTION = "tx"
    GET_TRANSACTIONS = "gettxs"
    TRANSACTIONS = "txs"
    KEY = "key"
