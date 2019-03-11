import platform
import socket

from bxcommon.utils.log_level import LogLevel

PLATFORM_LINUX = "linux"
PLATFORM_MAC = "darwin"
DEFAULT_TEXT_ENCODING = "utf-8"
LISTEN_ON_IP_ADDRESS = "0.0.0.0"
LOCALHOST = "127.0.0.1"
MAX_BYTE_VALUE = 255

HOSTNAME = socket.gethostname()
OS_VERSION = platform.platform()

# <editor-fold desc="Internal Constants">
ALL_NETWORK_NUM = 0
DEFAULT_NETWORK_NUM = 1

OUTPUT_BUFFER_MIN_SIZE = 65535
OUTPUT_BUFFER_BATCH_MAX_HOLD_TIME = 0.2

# The unsigned integer transaction SID representing null.
# If changing, also change in bxapi/constants.py
NULL_TX_SID = 0
# </editor-fold>

# <editor-fold desc="Connection Management">

# number of tries to resolve network address
NET_ADDR_INIT_CONNECT_TRIES = 3
NET_ADDR_INIT_CONNECT_RETRY_INTERVAL_SECONDS = 2

MAX_CONN_BY_IP = 30

# seconds interval between checking connection stances
CONNECTION_TIMEOUT = 3

MAX_CONNECT_RETRIES = 3
CONNECTION_RETRY_SECONDS = 5

RECV_BUFSIZE = 8192
MAX_BAD_MESSAGES = 3
PING_INTERVAL_S = 60
# </editor-fold>

# <editor-fold desc="Logging">
ENABLE_LOGGING = True

# set default log level use either enum values
# LogLevel.DEBUG
# LogLevel.INFO
# LogLevel.STATS
# LogLevel.WARN
# LogLevel.ERROR
# LogLevel.FATAL
# or their corresponding numbers
DEFAULT_LOG_LEVEL = LogLevel.INFO

# set to True to always flush logs to stdout
FLUSH_LOG = True

# </editor-fold>

# <editor-fold desc="Message Packing Constants">

UL_SHORT_SIZE_IN_BYTES = 2
UL_INT_SIZE_IN_BYTES = 4
IP_V4_PREFIX = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff")
IP_V4_PREFIX_LENGTH = 12
IP_ADDR_SIZE_IN_BYTES = 16
MSG_NULL_BYTE = "\x00"

# bytes of basic message header
HDR_COMMON_OFF = 16

# bytes for storing message type
MSG_TYPE_LEN = 12

NETWORK_NUM_LEN = UL_INT_SIZE_IN_BYTES
VERSION_NUM_LEN = UL_INT_SIZE_IN_BYTES
VERSIONED_HELLO_MSG_MIN_PAYLOAD_LEN = UL_INT_SIZE_IN_BYTES + NETWORK_NUM_LEN + VERSION_NUM_LEN

NODE_ID_SIZE_IN_BYTES = 16

NULL_ENCRYPT_REPEAT_VALUE = "1"  # must be nonzero string character
BLOXROUTE_HELLO_MESSAGES = ["hello", "ack"]

# </editor-fold>

# <editor-fold desc="SDN Constants">
SDN_ROOT_URL = "http://127.0.0.1:8080"
SDN_CONTACT_RETRY_SECONDS = 5


class SdnRoutes(object):
    nodes = "/nodes"
    node = "/nodes/{0}"
    node_relays = "/nodes/{0}/peers"
    node_potential_relays = "/nodes/{0}/potential_relays"
    node_gateways = "/nodes/{0}/gateways"
    node_remote_blockchain = "/nodes/blockchain-peers/{0}"
    node_event = "/nodes/{0}/events"
    blockchain_network = "/blockchain-networks/{0}/{1}"
    blockchain_networks = "/blockchain-networks"
    gateway_inbound_connection = "/nodes/{0}/gateway-inbound-connection"
    # TODO next sprint
    # sort_geo_location_traffic = "/geo_location_traffic/{0}"


# </editor-fold>

# <editor-fold desc="Stats Recording">

THROUGHPUT_STATS_INTERVAL = 30
THROUGHPUT_STATS_LOOK_BACK = 5

INFO_STATS_INTERVAL = 3600

# TODO: turn this number up to 60 minutes after we've done some testing to ensure that this is ok
MEMORY_STATS_INTERVAL = 3600

# Percentage for transactions that will be logged by stats service. The value should be controlled by SDN in the future.
TRANSACTIONS_PERCENTAGE_TO_LOG_STATS_FOR = 0.5
ENABLE_TRANSACTIONS_STATS_BY_SHORT_IDS = False

# </editor-fold>

# <editor-fold desc="Timers">
MAX_KQUEUE_EVENTS_COUNT = 1000
CANCEL_ALARMS = 0

# Fast execution timeout on alarm queue
DEFAULT_SLEEP_TIMEOUT = 0.1

REQUEST_EXPIRATION_TIME = 60

# Expiration time for block broadcast message if services info is missing
MISSING_BLOCK_EXPIRE_TIME = 60

# Expiration time for encrypted blocks in cache on relays and gateways
BLOCK_CACHE_TIMEOUT_S = 60 * 60

# Duration to warn on if alarm doesn't execute
WARN_ALARM_EXECUTION_DURATION = 5

# Timeout to warn on if alarm executed later than expected
WARN_ALARM_EXECUTION_OFFSET = 5
# </editor-fold>

# keep constants_local.py file to override settings in the constants file
# this part should be at the bottom of the file
try:
    from bxcommon.constants_local import *
except ImportError as e:
    pass
