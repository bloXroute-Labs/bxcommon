from bxutils.log_message_categories import *
from bxutils.logging_messages_utils import LogMessage

EMPTY_BLOCKCHAIN_NETWORK_LIST = LogMessage(
    "C-000000",
    REQUEST_RESPONSE_CATEGORY,
    "Empty list for blockchain networks from SDN, trying to obtain info from cache"
)
READ_CACHE_FILE_WARNING = LogMessage(
    "C-000001",
    GENERAL_CATEGORY,
    "Unable to find cache file: {}. Not using cache. You can disable caching by setting --enable-node-cache False."
)
PROTOCOL_VERSION_NOT_IN_FACTORY_MAPPING = LogMessage(
    "C-000002",
    REQUEST_RESPONSE_CATEGORY,
    "Got a message with version {}. Should be supported, but not in factory mapping."
)
UNABLE_TO_DETERMINE_PUBLIC_IP = LogMessage(
    "C-000003",
    NETWORK_CATEGORY,
    ("Unable to determine public IP address, please specify one manually via the '--external-ip' command line "
     "argument.\n\n Detailed error message:\n\t{}")
)
PING_TRIGGERED_AN_ERROR = LogMessage(
    "C-000004",
    NETWORK_CATEGORY,
    "Ping to {} {} triggered an error: {}."
)
ERROR_LOADING_MODEL_INTO_DICT = LogMessage(
    "C-000005",
    GENERAL_CATEGORY,
    "Failed when tried to load str to dict. model class: {} model params: {}"
)
STOP_RECORDING_CALLED_ON_UNINITIALIZED_THREAD = LogMessage(
    "C-000006",
    LOGGING_CATEGORY,
    "Thread was not initialized yet, but stop_recording was called. An invariant in the code is broken."
)
FAILURE_RECORDING_STATS = LogMessage(
    "C-000007",
    LOGGING_CATEGORY,
    "Recording {} stats failed with exception: {}. Stack trace: {}"
)
HTTP_REQUEST_RETURNED_ERROR = LogMessage(
    "C-000008",
    REQUEST_RESPONSE_CATEGORY,
    "{} to {} returned error: {}."
)
TASK_CANCELLED = LogMessage(
    "C-000009",
    THREAD_CATEGORY,
    "Task: {} with values: {} was cancelled: {}"
)
TASK_FAILED = LogMessage(
    "C-000010",
    THREAD_CATEGORY,
    "Task: {} with values: {} failed due to error: {}"
)
FLUENTD_LOGGER_BUFFER_OVERFLOW = LogMessage(
    "C-000011",
    LOGGING_CATEGORY,
    "fluentd logger, buffer overflow"
)
INVALID_LOG_LEVEL = LogMessage(
    "C-000012",
    LOGGING_CATEGORY,
    "Invalid Log Level Provided Ignore for path {}: {}"
)
DETECTED_PYTHON3_6 = LogMessage(
    "C-000013",
    GENERAL_CATEGORY,
    ("Python 3.6 environment is detected. Degraded performance is expected. Upgrade "
     "to Python 3.7 or above for improved performance.")
)
EMPTY_BLOCKCHAIN_NETWORK_CACHE = LogMessage(
    "C-000014",
    PROCESSING_FAILED_CATEGORY,
    "Cached info for blockchain_networks was empty"
)
DECRYPTION_FAILED = LogMessage(
    "C-000015",
    PROCESSING_FAILED_CATEGORY,
    "Could not decrypt encrypted item with hash {}. Last four bytes: {}"
)
UNABLE_TO_DETERMINE_CONNECTION_TYPE = LogMessage(
    "C-000016",
    CONNECTION_PROBLEM_CATEGORY,
    "Could not determine expected connection type for {}:{}. Disconnecting..."
)
FAILED_TO_AUTHENTICATE_CONNECTION = LogMessage(
    "C-000017",
    AUTHENTICATION_ERROR,
    "Failed to authenticate connection on {}:{} due to an error: {}."
)
ATTEMPTED_TO_ASSIGN_NULL_SHORT_ID_TO_TX_HASH = LogMessage(
    "C-000018",
    PROCESSING_FAILED_CATEGORY,
    "Attempted to assign null short id to transaction hash {}. Ignoring."
)
SID_MEMORY_MANAGEMENT_FAILURE = LogMessage(
    "C-000019",
    MEMORY_CATEGORY,
    "Memory management failure. There appears to be a lack of short ids in the node. Clearing all transaction data: {}"
)
UNABLE_TO_DETERMINE_TX_FINAL_CONFIRMATIONS_COUNT = LogMessage(
    "C-000020",
    PROCESSING_FAILED_CATEGORY,
    "Could not determine final confirmations count for network number {}. Using default {}."
)
UNABLE_TO_DETERMINE_TX_EXPIRATION_TIME = LogMessage(
    "C-000021",
    PROCESSING_FAILED_CATEGORY,
    "Could not determine expiration time for transaction removed from cache for network number {}. Using default {}."
)
TX_CACHE_SIZE_LIMIT_NOT_CONFIGURED = LogMessage(
    "C-000022",
    PROCESSING_FAILED_CATEGORY,
    "Blockchain network {} does not have tx cache size limit configured. Using default {}."
)
UNABLE_TO_DETERMINE_TX_MEMORY_LIMIT = LogMessage(
    "C-000023",
    MEMORY_CATEGORY,
    "Could not determine transactions memory limit for network number {}. Using default {}."
)
THREADED_REQUEST_HAS_LONG_RUNTIME = LogMessage(
    "C-000024",
    PROCESSING_FAILED_CATEGORY,
    "Threaded request was enqueued more than {} second(s) ago and hasn't finished yet: {}"
)
THREADED_REQUEST_IS_STALE = LogMessage(
    "C-000025",
    PROCESSING_FAILED_CATEGORY,
    "Threaded request hasn't started running yet, cancelling: {}"
)
BDN_RETURNED_NO_PEERS = LogMessage(
    "C-000026",
    REQUEST_RESPONSE_CATEGORY,
    "BDN returned no peers at endpoint: {}"
)
BDN_RETURNED_UNEXPECTED_NUMBER_OF_PEERS = LogMessage(
    "C-000027",
    REQUEST_RESPONSE_CATEGORY,
    "BDN did not send the expected number of remote blockchain peers."
)
BDN_CONTAINS_NO_CONFIGURED_NETWORKS = LogMessage(
    "C-000028",
    REQUEST_RESPONSE_CATEGORY,
    "BDN does not seem to contain any configured networks."
)
COULD_NOT_PARSE_MESSAGE = LogMessage(
    "C-000029",
    PROCESSING_FAILED_CATEGORY,
    "Could not parse message. Error: {}"
)
OUT_OF_MEMORY = LogMessage(
    "C-000030",
    PROCESSING_FAILED_CATEGORY,
    "Out of memory error occurred during message processing. Error: {}. "
)
UNAUTHORIZED_MESSAGE = LogMessage(
    "C-000031",
    PROCESSING_FAILED_CATEGORY,
    "Unauthorized message {} from {}."
)
UNABLE_TO_RECOVER_PARTIAL_MESSAGE = LogMessage(
    "C-000032",
    PROCESSING_FAILED_CATEGORY,
    "Unable to recover after message that failed validation. Closing connection."
)
TRYING_TO_RECOVER_MESSAGE = LogMessage(
    "C-000033",
    PROCESSING_FAILED_CATEGORY,
    "Message processing error; trying to recover. Error: {}."
)
UNABLE_TO_RECOVER_FULL_MESSAGE = LogMessage(
    "C-000034",
    PROCESSING_FAILED_CATEGORY,
    "Message processing error; unable to recover. Error: {}."
)
UNEXPECTED_MESSAGE = LogMessage(
    "C-000035",
    PROCESSING_FAILED_CATEGORY,
    "Received unexpected message ({}) before handshake completed. Closing."
)
MESSAGE_VALIDATION_FAILED = LogMessage(
    "C-000036",
    PROCESSING_FAILED_CATEGORY,
    "Message validation failed for {} message: {}."
)
INVALID_HANDSHAKE = LogMessage(
    "C-000037",
    PROCESSING_FAILED_CATEGORY,
    "Invalid handshake request on {}:{}. Rejecting the connection. {}"
)
DUPLICATE_CONNECTION = LogMessage(
    "C-000038",
    PROCESSING_FAILED_CATEGORY,
    "Discovered duplicate connections to node {}: {}. Closing."
)
TOO_MANY_BAD_MESSAGES = LogMessage(
    "C-000039",
    PROCESSING_FAILED_CATEGORY,
    "Received too many bad messages. Closing."
)
NETWORK_NUMBER_MISMATCH = LogMessage(
    "C-000040",
    PROCESSING_FAILED_CATEGORY,
    "Network number mismatch. Current network num {}, remote network num {}. Closing connection."
)
RPC_COULD_NOT_PARSE_TRANSACTION = LogMessage(
    "C-000041",
    REQUEST_RESPONSE_CATEGORY,
    "Error parsing the transaction:\n{}",
)
INTERNAL_ERROR_HANDLING_RPC_REQUEST = LogMessage(
    "C-000042",
    RPC_ERROR,
    "Internal error {} while handling request {}"
)
BDN_ACCOUNT_INFORMATION_TIMEOUT = LogMessage(
    "C-000043",
    CONNECTION_PROBLEM_CATEGORY,
    "BDN does not send the account information within {} seconds."
)

NODE_RECEIVED_TX_WITH_INVALID_FORMAT = LogMessage(
    "C-000044",
    GENERAL_CATEGORY,
    "{} received transaction {} from {} with an invalid format"
)

NODE_RECEIVED_TX_WITH_INVALID_SIG = LogMessage(
    "C-000045",
    GENERAL_WARNING,
    "{} received transaction {} from {} with an invalid signature"
)
MISSING_ASSIGN_TIME_FOR_SHORT_ID = LogMessage(
    "C-000046",
    GENERAL_CATEGORY,
    "Missing assignment time for short id {}."
)
WS_COULD_NOT_CONNECT = LogMessage(
    "C-000047",
    CONNECTION_PROBLEM_CATEGORY,
    "Could not connect to websockets server at {}. Connection timed out.",
)
ETH_RPC_ERROR = LogMessage(
    "C-000048",
    PROCESSING_FAILED_CATEGORY,
    "RPC Error response: {}. details: {}.",
)
ETH_RPC_PROCESSING_ERROR = LogMessage(
    "C-000049",
    PROCESSING_FAILED_CATEGORY,
    "Encountered exception when processing message: {}. Error: {}. Continuing processing.",
)
ETH_WS_SUBSCRIBER_CONNECTION_BROKEN = LogMessage(
    "C-000050",
    RPC_ERROR,
    "Ethereum websockets connection was broken. Attempting reconnection..."
)
ETH_RPC_COULD_NOT_RECONNECT = LogMessage(
    "C-000051",
    CONNECTION_PROBLEM_CATEGORY,
    "Could not reconnect to Ethereum websockets feed. Disabling Ethereum transaction "
    "verification for now, but will attempt reconnection upon when the next subscriber "
    "reconnects."
)
MSG_PROXY_REQUESTER_QUEUE_EMPTY_ON_RESPONSE = LogMessage(
    "C-000052",
    GENERAL_CATEGORY,
    "Message proxy requester queue empty upon receiving response from remote blockchain "
    "node. Unable to forward response to blockchain node."
)
RPC_TRANSPORT_EXCEPTION = LogMessage(
    "C-000053",
    CONNECTION_PROBLEM_CATEGORY,
    "Websocket disconnected due to transport layer exception: {}",
)
BAD_RPC_SUBSCRIBER = LogMessage(
    "C-000054",
    RPC_ERROR,
    "Subscription message queue was completed filled up (size {}). "
    "Closing subscription RPC handler and all related subscriptions: {}"
)
COULD_NOT_SERIALIZE_FEED_ENTRY = LogMessage(
    "C-000055",
    PROCESSING_FAILED_CATEGORY,
    "Could not serialize feed entry. Skipping."
)
BAD_FEED_SUBSCRIBER = LogMessage(
    "C-000056",
    GENERAL_CATEGORY,
    "Subscriber {} was not receiving messages and emptying its queue from "
    "{}. Disconnecting.",
)
WS_COULD_NOT_CONNECT_AFTER_RETRIES = LogMessage(
    "C-000057",
    CONNECTION_PROBLEM_CATEGORY,
    "Could not connect to websockets server at {}. Connection timed out. Tried {} times.",
)
WS_UNEXPECTED_ERROR = LogMessage(
    "C-000058",
    CONNECTION_PROBLEM_CATEGORY,
    "Unexpected logger connection error: {}. Retrying connection."
)
WS_COULD_NOT_PROCESS_NOTIFICATION = LogMessage(
    "C-000059",
    PROCESSING_FAILED_CATEGORY,
    "Unexpected error in feed callback: {}."
)