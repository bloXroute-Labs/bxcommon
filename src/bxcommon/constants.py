import os
import platform
import socket

PLATFORM_LINUX = "linux"
PLATFORM_MAC = "darwin"
DEFAULT_TEXT_ENCODING = "utf-8"
LISTEN_ON_IP_ADDRESS = "0.0.0.0"
DEFAULT_NODE_BACKLOG: int = 500
LOCALHOST = "127.0.0.1"
MAX_BYTE_VALUE = 255

PUBLIC_IP_ADDR_REGEX = r"[0-9]+(?:\.[0-9]+){3}"
PUBLIC_IP_ADDR_RESOLVER = "http://checkip.dyndns.org/"

NODE_CONFIG_FILE = "config.cfg"
BLXR_ENV_VAR = "BLXR_ENV"

HOSTNAME = socket.gethostname()
OS_VERSION = platform.platform()

MANIFEST_PATH = "MANIFEST.MF"
MANIFEST_SOURCE_VERSION = "source_version"
PROTOCOL_VERSION = "protocol_version"
REQUIRED_PARAMS_IN_MANIFEST = [MANIFEST_SOURCE_VERSION]
VERSION_TYPE_LIST = ["dev", "v", "ci"]

# <editor-fold desc="Internal Constants">
ALL_NETWORK_NUM = 0
DEFAULT_NETWORK_NUM = 1

OUTPUT_BUFFER_MIN_SIZE = 65535
OUTPUT_BUFFER_BATCH_MAX_HOLD_TIME = 0.05

FULL_QUOTA_PERCENTAGE = 100

WS_PROVIDER_MAX_QUEUE_SIZE = 1000
WS_MIN_RECONNECT_TIMEOUT_S = 1
WS_RECONNECT_TIMEOUTS = [1, 2, 3, 5, 8, 13]
WS_MAX_CONNECTION_TIMEOUT_S = 2

# The unsigned integer transaction SID representing null.
# If changing, also change in bxapi/constants.py
NULL_TX_SID = 0
NULL_TX_SIDS = {NULL_TX_SID}
NULL_TX_TIMESTAMP = 0
TX_SID_INTERVAL = 10000000
# </editor-fold>

# <editor-fold desc="Connection Management">

# number of tries to resolve network address
NET_ADDR_INIT_CONNECT_TRIES = 3
NET_ADDR_INIT_CONNECT_RETRY_INTERVAL_SECONDS = 2

MAX_CONN_BY_IP = 30

# seconds interval between checking connection stances
CONNECTION_TIMEOUT = 3

MAX_CONNECT_RETRIES = 3
MAX_CONNECT_TIMEOUT_INCREASE = 7

RECV_BUFSIZE = 1024 * 1024
MAX_BAD_MESSAGES = 3
PING_INTERVAL_S = 60
PING_PONG_TRESHOLD = 0.5
# </editor-fold>

# <editor-fold desc="Logging">

MAX_LOGGED_BYTES_LEN = 500 * 1024

# </editor-fold>

# <editor-fold desc="Message Packing Constants">

STARTING_SEQUENCE_BYTES = bytearray(b"\xFF\xFE\xFD\xFC")
STARTING_SEQUENCE_BYTES_LEN = 4
CONTROL_FLAGS_LEN = 1
UL_TINY_SIZE_IN_BYTES = 1
UL_SHORT_SIZE_IN_BYTES = 2
UL_INT_SIZE_IN_BYTES = 4
UL_ULL_SIZE_IN_BYTES = 8
DOUBLE_SIZE_IN_BYTES = 8
UNSIGNED_SHORT_MAX_VALUE = 65535
UNSIGNED_INT_MAX_VALUE = 4294967295
IP_V4_PREFIX = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff")
IP_V4_PREFIX_LENGTH = 12
IP_ADDR_SIZE_IN_BYTES = 16
MSG_NULL_BYTE = b"\x00"

# bytes of basic message header
BX_HDR_COMMON_OFF = 16

# bytes for storing message type
MSG_TYPE_LEN = 12

QUOTA_FLAG_LEN = UL_TINY_SIZE_IN_BYTES
SID_LEN = UL_INT_SIZE_IN_BYTES
TRANSACTION_FLAG_LEN = UL_SHORT_SIZE_IN_BYTES

SID_EXPIRE_TIME_SECONDS = 3 * 24 * 60 * 60

BLOCK_ENCRYPTED_FLAG_LEN = 1
BROADCAST_TYPE_LEN = 4

NETWORK_NUM_LEN = UL_INT_SIZE_IN_BYTES
VERSION_NUM_LEN = UL_INT_SIZE_IN_BYTES
VERSIONED_HELLO_MSG_MIN_PAYLOAD_LEN = UL_INT_SIZE_IN_BYTES + NETWORK_NUM_LEN + VERSION_NUM_LEN

NODE_ID_SIZE_IN_BYTES = 16
ACCOUNT_ID_SIZE_IN_BYTES = 36

NULL_ENCRYPT_REPEAT_VALUE = "1"  # must be nonzero string character
BLOXROUTE_HELLO_MESSAGES = [b"hello", b"ack"]
HTTP_MESSAGE = b"HTTP"
BITCOIN_MESSAGES = [b"\x03\x00\x00/*\xe0\x00\x00\x00\x00\x00C", b"\xff\x00d\x00\x00\x00\x01"]
# </editor-fold>

# <editor-fold desc="SDN Constants">
SDN_ROOT_URL = "https://127.0.0.1:8080"
SDN_CONTACT_RETRY_SECONDS = 5
MAX_COUNTRY_LENGTH = 30

# Should use extension modules
USE_EXTENSION_MODULES = True

# Should support compact block message
ACCEPT_COMPACT_BLOCK = True

DUMP_MISSING_SHORT_IDS_PATH = "/app/bxrelay/debug/missing-short-ids"


class SdnRoutes:
    nodes = "/nodes"
    node = "/nodes/{0}"
    account = "/account/{0}"
    node_potential_relays_by_network = "/nodes/{0}/{1}/potential-relays"
    node_gateways = "/nodes/{0}/gateways?streaming={1}"
    node_remote_blockchain = "/nodes/{0}/potential-remote-blockchain-peers"
    node_event = "/nodes/{0}/events"
    blockchain_network = "/blockchain-networks/{0}/{1}"
    blockchain_networks = "/blockchain-networks"
    gateway_inbound_connection = "/nodes/{0}/gateway-inbound-connection"
    bdn_services = "/configs/bdn-services"
    quota_status = "/accounts/quota-status"
    gateway_settings = "/nodes/{0}/gateway-settings"


# </editor-fold>

# <editor-fold desc="Stats Recording">
FIRST_STATS_INTERVAL_S = 5 * 60

THROUGHPUT_STATS_INTERVAL_S = 15
THROUGHPUT_STATS_LOOK_BACK = 5

NODE_STATS_INTERVAL_S = 60

INFO_STATS_INTERVAL_S = 60 * 60

# how often the threaded stats services check for termination
THREADED_STATS_SLEEP_INTERVAL_S = 1

THREAD_POOL_WORKER_COUNT = (os.cpu_count() or 1) * 5
THREADED_HTTP_POOL_SLEEP_INTERVAL_S = 60
HTTP_POOL_MANAGER_COUNT = 1

# TODO: turn this number up to 60 minutes after we've done some testing to ensure that this is ok
MEMORY_STATS_INTERVAL_S = 30 * 60
MEMORY_USAGE_INCREASE_FOR_NEXT_REPORT_BYTES = 1024 * 1024 * 1024

# Percentage for transactions that will be logged by stats service. The value should be controlled by SDN in the future.
TRANSACTIONS_BY_HASH_PERCENTAGE_TO_LOG_STATS_FOR = 0.1
TRANSACTIONS_BY_SID_PERCENTAGE_TO_LOG_STATS_FOR = 0.01
ENABLE_TRANSACTIONS_STATS_BY_SHORT_IDS = False
DEFAULT_THREAD_POOL_PARALLELISM_DEGREE = 1
DEFAULT_TX_MEM_POOL_BUCKET_SIZE = 10000

# </editor-fold>

# <editor-fold desc="Timers">
MAX_KQUEUE_EVENTS_COUNT = 1000
CANCEL_ALARMS = 0

# Fast execution timeout on alarm queue
MIN_SLEEP_TIMEOUT = 0.1

REQUEST_EXPIRATION_TIME = 15 * 60  # TODO: Return this value to 1 minute

# Expiration time for encrypted blocks in cache on relays and gateways
BLOCK_CACHE_TIMEOUT_S = 60 * 60

# Duration to warn on if alarm doesn't execute
WARN_ALARM_EXECUTION_DURATION = 0.2
WARN_ALL_ALARMS_EXECUTION_DURATION = 0.5

# Timeout to warn on if alarm executed later than expected
WARN_ALARM_EXECUTION_OFFSET = 5

# Minimal expired transactions clean up task frequency
MIN_CLEAN_UP_EXPIRED_TXS_TASK_INTERVAL_S = 15

# Duration to warn on if message processing takes longer than
WARN_MESSAGE_PROCESSING_S = 0.1

# Expiration time for cache of relayed blocks hashes
RELAYED_BLOCKS_EXPIRE_TIME_S = 6 * 60 * 60

DUMP_REMOVED_SHORT_IDS_INTERVAL_S = 5 * 60
DUMP_REMOVED_SHORT_IDS_PATH = "/app/bxcommon/debug/removed-short-ids"

CLEAN_UP_SEEN_SHORT_IDS_DELAY_S = 10

REMOVED_TRANSACTIONS_HISTORY_EXPIRATION_S = 6 * 60 * 60
REMOVED_TRANSACTIONS_HISTORY_CLEANUP_INTERVAL_S = 10
REMOVED_TRANSACTIONS_HISTORY_LENGTH_LIMIT = 500000

RESPONSIVENESS_CHECK_INTERVAL_S = 1
RESPONSIVENESS_CHECK_DELAY_WARN_THRESHOLD_S = 0.2
MEMORY_STATS_DURATION_WARN_THRESHOLD_S = 0.2
MSG_HANDLERS_CYCLE_DURATION_WARN_THRESHOLD_S = 0.2
MSG_HANDLERS_DURATION_WARN_THRESHOLD_S = 0.5
NETWORK_OPERATION_CYCLE_DURATION_WARN_THRESHOLD_S = 0.2
NETWORK_OPERATION_DURATION_WARN_THRESHOLD_S = 0.5
GC_DURATION_WARN_THRESHOLD = 0.1
TX_SERVICE_SET_TXS_WARN_THRESHOLD = 0.1

SERIALIZED_MESSAGE_CACHE_EXPIRE_TIME_S = 10
USE_SERIALIZED_MESSAGE_CACHE = False

# </editor-fold>

# <editor-fold desc="Default Values">

# Default transactions contents cache maximum size per network number
DEFAULT_TX_CACHE_MEMORY_LIMIT_BYTES = 250 * 1024 * 1024

# Default maximum allowed length of internal message payload
DEFAULT_MAX_PAYLOAD_LEN_BYTES = 1024 * 1024

# cleanup confirmed blocks in this depth
BLOCK_CONFIRMATIONS_COUNT = 4

DEFAULT_BLOCK_HOLD_TIMEOUT = 0.3

TXS_MSG_SIZE = 64000
TXS_SYNC_TASK_DURATION = 0.15
TX_SERVICE_SYNC_TXS_S = 0.01
SENDING_TX_MSGS_TIMEOUT_S = 15 * 60
TX_SERVICE_CHECK_NETWORKS_SYNCED_S = 10 * 60
LAST_MSG_FROM_RELAY_THRESHOLD_S = 30
PING_TIMEOUT_S = 2

GATEWAY_SWAP_RELAYS_LATENCY_THRESHOLD_MS = 3
NODE_LATENCY_THRESHOLD_MS = 2
FASTEST_PING_LATENCY_THRESHOLD_PERCENT = 0.2
UPDATE_TX_SERVICE_FULLY_SYNCED_S = 1
FIRST_TX_SERVICE_SYNC_PROGRESS_S = 1
TX_SERVICE_SYNC_PROGRESS_S = 10
TX_SERVICE_SYNC_RELAY_IN_NETWORKS_S = 30

ALARM_QUEUE_INIT_EVENT = 1

# extensions memory management params
MAX_ALLOCATION_POINTER_COUNT = 10
MAX_COUNT_PER_ALLOCATION = 10

EMPTY_SOURCE_ID = MSG_NULL_BYTE * 16
DECODED_EMPTY_SOURCE_ID = EMPTY_SOURCE_ID.decode()

TRANSACTION_SERVICE_LOG_TRANSACTIONS_INTERVAL_S = 60 * 15
TRANSACTION_SERVICE_TRANSACTIONS_HISTOGRAM_BUCKETS = 36

EMPTY_ACCOUNT_ID = MSG_NULL_BYTE * 36
DECODED_EMPTY_ACCOUNT_ID = EMPTY_ACCOUNT_ID.decode()

# https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#module-urllib3.util.retry
HTTP_REQUEST_RETRIES_COUNT: int = 3
HTTP_REQUEST_BACKOFF_FACTOR: float = 0.5
HTTP_REQUEST_TIMEOUT: int = 5
HTTP_HEADERS = {"Content-Type": "application/json"}

MAX_EVENT_LOOP_TIMEOUT: float = 0.05

MAX_EXPIRED_TXS_TO_REMOVE = 500

# </editor-fold>

# keep constants_local.py file to override settings in the constants file
# this part should be at the bottom of the file
try:
    # pyre-ignore
    from bxcommon.constants_local import *
except ImportError as e:
    pass

DEFAULT_LIST_LOCATION_ORDER = ["NA", "SA", "EU", "OC", "AS", "AF", "AN"]
DEFAULT_NETWORK_NAME = "bxtest"

UNASSIGNED_NETWORK_NUMBER = -1

PING_PONG_REPLY_TIMEOUT_S = 5 * 60

NODE_COUNTRY_ATTRIBUTE_NAME = "country"
NODE_REGION_ATTRIBUTE_NAME = "region"
NODE_COUNTRY_CHINA = "China"

NODE_SHUTDOWN_TIMEOUT_S = 30

# tx gateway sync snapshot interval, 0 to snapshot the whole mempool
GATEWAY_SYNC_TX_THRESHOLD_S = 30 * 60
GATEWAY_SYNC_SYNC_CONTENT = True
GATEWAY_SYNC_BUILD_MESSAGE_THRESHOLD_S = 0.15
GATEWAY_SYNC_MAX_MESSAGE_SIZE_BYTES = 500 * 1024
TX_CONTENT_NO_SID_EXPIRE_S = 60 * 15
TX_SYNC_USE_SNAPSHOT = False

BYTE_TO_MB = 1024 * 1024

MEM_STATS_OBJECT_SIZE_THRESHOLD = 1024 * 1024
MEM_STATS_OBJECT_COUNT_THRESHOLD = 2000

TX_FROM_PUB_API_TO_RELAY_THRESHOLD_S = 2.0
TRANSACTION_STREAMER_ATTRIBUTE_NAME = "tx_streamer"
PRIVATE_IP_ATTRIBUTE_NAME = "using_private_ip"

EPOCH_DATE: str = "1970-01-01"
END_DATE: str = "2999-01-01"

RPC_SUBSCRIBER_MAX_QUEUE_SIZE = 1000

WS_DEFAULT_PORT = 28332

GC_LOW_MEMORY_THRESHOLD = 1024 * 1024 * 1024 * 3
GC_MEDIUM_MEMORY_THRESHOLD = 1024 * 1024 * 1024 * 3.5
GC_HIGH_MEMORY_THRESHOLD = 1024 * 1024 * 1024 * 4

BLOCKS_FAILED_VALIDATION_HISTORY_SIZE = 10

THROTTLE_RECONNECT_TIME_S = 15 * 60
MAX_HIGH_RECONNECT_ATTEMPTS_ALLOWED = 10

WAIT_FOR_SUBSCRIPTION_TIMEOUT = 60
