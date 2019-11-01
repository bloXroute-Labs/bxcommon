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
    DISCONNECT_RELAY_PEER = b"droprelay"
    TX_SERVICE_SYNC_REQ = b"txstart"
    TX_SERVICE_SYNC_BLOCKS_SHORT_IDS = b"txblock"
    TX_SERVICE_SYNC_TXS = b"txtxs"
    TX_SERVICE_SYNC_COMPLETE = b"txdone"
    BLOCK_CONFIRMATION = b"blkcnfrm"
    TRANSACTION_CLEANUP = b"txclnup"
