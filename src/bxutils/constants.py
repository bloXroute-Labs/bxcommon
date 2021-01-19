from datetime import datetime, date, timedelta

from bxcommon.utils.port_range import PortRange
from bxutils.logging.fluentd_overflow_handler_type import OverflowHandlerType
from bxutils.logging.log_format import LogFormat
from bxutils.logging.log_level import LogLevel

DEFAULT_LOG_LEVEL = LogLevel.INFO
DEFAULT_STATS_LOG_LEVEL = LogLevel.CRITICAL
STATS_LOGGER_NAMES = ["stats", "bx"]

# Log Format from Python3 Logging Package
#
#   %(name)s            Name of the logger (logging channel)
#   %(levelno)s         Numeric logging level for the message (DEBUG, INFO,
#                       WARNING, ERROR, CRITICAL)
#   %(levelname)s       Text logging level for the message ("DEBUG", "INFO",
#                       "WARNING", "ERROR", "CRITICAL")
#   %(pathname)s        Full pathname of the source file where the logging
#                       call was issued (if available)
#   %(filename)s        Filename portion of pathname
#   %(module)s          Module (name portion of filename)
#   %(lineno)d          Source line number where the logging call was issued
#                       (if available)
#   %(funcName)s        Function name
#   %(created)f         Time when the LogRecord was created (time.time()
#                       return value)
#   %(asctime)s         Textual time when the LogRecord was created
#   %(msecs)d           Millisecond portion of the creation time
#   %(relativeCreated)d Time in milliseconds when the LogRecord was created,
#                       relative to the time the logging module was loaded
#                       (typically at application startup time)
#   %(thread)d          Thread ID (if available)
#   %(threadName)s      Thread name (if available)
#   %(process)d         Process ID (if available)
#   %(message)s         The result of record.getMessage(), computed just as
#                       the record is emitted
DEBUG_LOG_FORMAT_PATTERN = "%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s"
INFO_LOG_FORMAT_PATTERN = "%(asctime)s - %(levelname)s - %(message)s"
PLAIN_LOG_DATE_FORMAT_PATTERN = "%Y-%m-%dT%H:%M:%S.%f %z"
DEFAULT_LOG_FORMAT = LogFormat.PLAIN
FLUENTD_HOST = None
FLUENTD_PORT = 24224
FLUENTD_OVERFLOW_HANDLER = OverflowHandlerType.Print
FLUENTD_LOGGER_MAX_QUEUE_SIZE = 2 * 1024 * 1024

FLUENTD_DEFAULT_TAG = "bx"

# ssl constants

# TODO: use the data dir configurations (https://github.com/bloXroute-Labs/bxcommon-private/pull/510) after merging
#  bxutils back into bxcommon
DEFAULT_EXPIRATION_DATE: date = datetime.today().date() + timedelta(365)
SSL_FOLDER = ".ssl"
SSL_KEY_FILE_FORMAT = "{}_key.pem"
SSL_CERT_FILE_FORMAT = "{}_cert.pem"
DEFAULT_PUBLIC_CA_URL = "https://s3.amazonaws.com/credentials.blxrbdn.com/"
DEFAULT_CERTIFICATE_RENEWAL_PERIOD_DAYS: int = 10
SSL_PORT_RANGE: PortRange = PortRange(1800, 2000)
DEFAULT_NODE_PRIVILEGES = "general"

DEFAULT_SDN_SOCKET_PORT = 1800

CATEGORIZED_LOG_LEVELS = ["ERROR", "WARNING"]
HAS_PREFIX = "with_logging_prefix"

FIBONACCI_GOLDEN_RATIO = (1 + 5 ** .5) / 2
