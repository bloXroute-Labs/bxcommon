from enum import Enum

CONTENT_TYPE_HEADER_KEY = "Content-Type"
ACCEPT_HEADER_KEY = "Accept"
PLAIN_HEADER_TYPE = "text/plain"
JSON_HEADER_TYPE = "application/json"
OCTET_STREAM_HEADER_TYPE = "application/octet-stream"
TRANSACTION_HASH_PARAMS_KEY = "transaction_hash"
TRANSACTION_PARAMS_KEY = "transaction"
TRANSACTION_VARIATIONS_PARAMS_KEY = "transactions"
TRANSACTION_FEE_BUMP_INTERVAL_S = "bump_interval"
TRANSACTION_JSON_PARAMS_KEY = "transaction_json"
TRANSACTION_FLAG_PARAMS_KEY = "transaction_flag"
PRIVATE_TRANSACTION_TIMEOUT_KEY = "timeout"
TAG_PARAMS_KEY = "tag"
SYNCHRONOUS_PARAMS_KEY = "synchronous"
STATUS_TRACK_PARAMS_KEY = "status_track"
NONCE_MONITORING_PARAMS_KEY = "nonce_monitoring"
DETAILS_LEVEL_PARAMS_KEY = "details_level"
BLOCKCHAIN_PROTOCOL_PARAMS_KEY = "blockchain_protocol"
BLOCKCHAIN_NETWORK_PARAMS_KEY = "blockchain_network"
BLOCKCHAIN_NETWORK_NUM_PARAMS_KEY = "blockchain_network_num"
NETWORK_NUM_PARAMS_KEY = "network_num"
ACCOUNT_ID_PARAMS_KEY = "account_id"
ACCOUNT_CACHE_KEY_PARAMS_KEY = "account_cache_key"
TX_SERVICE_FILE_NAME_PARAMS_KEY = "file_name"
BLOCKCHAIN_PEER_PARAMS_KEY = "peer"
AUTHORIZATION_HEADER_KEY = "Authorization"
WEBSOCKET_HEADER_KEY = "upgrade"
RPC_SERVER_INIT_TIMEOUT_S = 10
RPC_SERVER_STOP_TIMEOUT_S = 10
HEALTHCHECK_INTERVAL = 60
DEFAULT_RPC_PORT = 28332
DEFAULT_RPC_HOST = "127.0.0.1"
DOCKER_RPC_HOST = "172.17.0.1"
DEFAULT_RPC_USER = ""
DEFAULT_RPC_PASSWORD = ""
DEFAULT_RPC_BASE_SSL_URL = ""
MAINNET_NETWORK_NAME = "Mainnet"
CLOUD_API_URL = "https://api.blxrbdn.com"

JSON_RPC_VERSION = "2.0"
JSON_RPC_REQUEST_ID = "id"
JSON_RPC_METHOD = "method"
JSON_RPC_PARAMS = "params"
JSON_RPC_VERSION_FIELD = "jsonrpc"
JSON_RPC_RESULT = "result"
JSON_RPC_ERROR = "error"
JSON_RPC_MESSAGE = "message"
JSON_RPC_DATA = "data"

NEW_TRANSACTION_FEED_NAME = "newTxs"
NEW_BLOCKS_FEED_NAME = "newBlocks"
ETH_ON_BLOCK_FEED_NAME = "ethOnBlock"
ETH_PENDING_TRANSACTION_FEED_NAME = "pendingTxs"
TRANSACTION_STATUS_FEED_NAME = "transactionStatus"


class ContentType(Enum):
    PLAIN = PLAIN_HEADER_TYPE
    JSON = JSON_HEADER_TYPE

    @classmethod
    def from_string(cls, s: str) -> "ContentType":
        for val in cls:
            if val.value == s:
                return val
        raise ValueError(f"{s} is not a valid {cls}.")
