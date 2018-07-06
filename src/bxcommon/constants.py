import hashlib

sha256 = hashlib.sha256

MAX_CONN_BY_IP = 30  # Maximum number of connections that an IP address can have

CONNECTION_TIMEOUT = 30  # Number of seconds that we wait to retry a connection.
FAST_RETRY = 3  # Seconds before we retry in case of transient failure (e.g. EINTR thrown)
MAX_RETRIES = 10

# Number of bad messages I'm willing to receive in a row before declaring the input stream
# corrupt beyond repair.
MAX_BAD_MESSAGES = 3

# The size of the recv buffer that we fill each time.
RECV_BUFSIZE = 8192

RETRY_INTERVAL = 30  # Seconds before we retry in case of orderly shutdown

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

# If the peer is more this many blocks behind me, then we close the connection.
# This is useful to change for testing so that we can test tranfer rates for large numbers of blocks.
HEIGHT_DIFFERENCE = 100

FLUSH_LOG = False
