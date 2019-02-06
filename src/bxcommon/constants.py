import platform
import socket

from bxcommon.utils.log_level import LogLevel

HOSTNAME = socket.gethostname()
OS_VERSION = platform.platform()

MAX_CONN_BY_IP = 30  # Maximum number of connections that an IP address can have

CONNECTION_TIMEOUT = 3  # Number of seconds that we wait to retry a connection.
MAX_CONNECT_RETRIES = 3

# Number of bad messages I'm willing to receive in a row before declaring the input stream
# corrupt beyond repair.
MAX_BAD_MESSAGES = 3

# Number of tries to connect to a peer on startup
NET_ADDR_INIT_CONNECT_TRIES = 3
NET_ADDR_INIT_CONNECT_RETRY_INTERVAL_SECONDS = 2

# The size of the recv buffer that we fill each time.
RECV_BUFSIZE = 8192

CONNECTION_RETRY_SECONDS = 5  # Seconds to wait before retrying connection.

SINK_TIMEOUT_SECONDS = 60  # Seconds timeout for the sink

# Number of messages that can be cut through at a time
MAX_CUT_THROUGH_SEND_QUEUE = 5000

# Number of messages that can be kept in the history at a time.
# Two identical messages that are broadcast more than MAX_MESSAGE_HISTORY messages apart
# will both be cut through broadcast.
MAX_MESSAGE_HISTORY = 5000

# True if we want to avoid doing the database puts
FAKE_DB = False

# True if we want to take heap profiles
PROFILING = False

# negative if we are never going to crash
# Otherwise, it's the number of seconds until this bloxroute node
# will crash.
CRASH_INTERVAL = -1

LOG_FOR_WEB = True

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

# If the peer is more this many blocks behind me, then we close the connection.
# This is useful to change for testing so that we can test tranfer rates for large numbers of blocks.
HEIGHT_DIFFERENCE = 100

FLUSH_LOG = True

LISTEN_ON_IP_ADDRESS = "0.0.0.0"
LOCALHOST = "127.0.0.1"

# The length of everything in the header minus the checksum
HDR_COMMON_OFF = 16

MSG_TYPE_LEN = 12

UL_SHORT_SIZE_IN_BYTES = 2
# Size of integer in bytes
UL_INT_SIZE_IN_BYTES = 4  # If changing here, also change in bxapi/constants.py

IP_V4_PREFIX = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff")
IP_V4_PREFIX_LENGTH = 12
IP_ADDR_SIZE_IN_BYTES = 16

# Length of network number in messages in bytes
NETWORK_NUM_LEN = UL_INT_SIZE_IN_BYTES

# Expiration time for block broadcast message if services info is missing
MISSING_BLOCK_EXPIRE_TIME = 60

CUT_THROUGH_TIMEOUT = 60  # Maximum time (in seconds) that we wait for the remote to send us this block
MGR_DELETE_DELAY = 100  # Time (in seconds) we wait until we delete this manager from our node.

MIN_PYLINT_SCORE = 9.5

PING_INTERVAL_SEC = 60

# The unsigned integer transaction SID representing null.
NULL_TX_SID = 0  # If changing, also change in bxapi/constants.py
SID_RANGE_EARLY_UPDATE_PERCENT = .9

# Unsigned int used for no idx in hello messages from gateways.
NULL_IDX = 0  # If changing, also change in bxapi/constants.

PLATFORM_LINUX = "linux"
PLATFORM_MAC = "darwin"

DEFAULT_SLEEP_TIMEOUT = 0.1  # Schedule an event to be executed fast on alarm queue.

MAX_KQUEUE_EVENTS_COUNT = 1000

BX_API_ROOT_URL = "http://127.0.0.1:8080"


class BxApiRoutes(object):
    nodes = "/nodes"
    node = "/nodes/{0}"
    node_relays = "/nodes/{0}/peers"
    node_gateways = "/nodes/{0}/gateways"
    node_remote_blockchain = "/nodes/blockchain-peers/{0}"
    node_event = "/nodes/{0}/events"
    blockchain_network = "/blockchain-networks/{0}/{1}"
    blockchain_networks = "/blockchain-networks"


SDN_CONTACT_RETRY_SECONDS = 5

# Time (in seconds) between stats gathering runs
THROUGHPUT_STATS_INTERVAL = 300
# Look back limit (in seconds) - Stats older then this will be discarded (Should be >= THROUGHPUT_STATS_INTERVAL)
THROUGHPUT_STATS_LOOK_BACK = 600
MSG_NULL_BYTE = "\x00"
NULL_ENCRYPT_REPEAT_VALUE = "1"  # must be nonzero string character
BLOXROUTE_HELLO_MESSAGES = ["hello", "ack"]

DEFAULT_TEXT_ENCODING = "utf-8"

VERSION_NUM_LEN = UL_INT_SIZE_IN_BYTES
VERSIONED_HELLO_MSG_MIN_PAYLOAD_LEN = UL_INT_SIZE_IN_BYTES + NETWORK_NUM_LEN + VERSION_NUM_LEN

ALL_NETWORK_NUM = 0
DEFAULT_NETWORK_NUM = 1

OUTPUT_BUFFER_MIN_SIZE = 65535
OUTPUT_BUFFER_BATCH_MAX_HOLD_TIME = 0.2

RELAY_PING_INTERVAL_S = 2
RELAY_KEY_EXPIRATION_TIME_S = 30 * 60

# Time (in seconds) between stats gathering runs
INFO_STATS_INTERVAL = 3600
MEMORY_STATS_INTERVAL = 300

# return timeout in abstract node
CANCEL_ALARMS = 0

NODE_ID_SIZE_IN_BYTES = 16

REQUEST_EXPIRATION_TIME = 60

# keep constants_local.py file to override settings in the constants file
# this part should be at the bottom of the file
try:
    from bxcommon.constants_local import *
except ImportError as e:
    pass

