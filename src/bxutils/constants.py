from bxutils.logging.log_format import LogFormat
from bxutils.logging.log_level import LogLevel

DEFAULT_LOG_LEVEL = LogLevel.INFO

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
DEFAULT_LOG_FORMAT = LogFormat.PLAIN
