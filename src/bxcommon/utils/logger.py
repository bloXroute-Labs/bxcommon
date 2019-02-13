import os
import sys
import threading
import time
from collections import deque
from datetime import datetime
from threading import Condition, Lock, Thread

from bxcommon.constants import ENABLE_LOGGING, FLUSH_LOG, DEFAULT_LOG_LEVEL
from bxcommon.utils.log_level import LogLevel

##
# The Logging Interface
##


DUMP_LOG = False
MAX_ERR_QUEUE_SIZE = 30

error_msgs = deque()
_hostname = '[Unassigned]'
_log_level = DEFAULT_LOG_LEVEL
_default_log = None
# The time (in seconds) to cycle through to another log.
LOG_ROTATION_INTERVAL = 24 * 3600


# Log class that you can write to which asynchronously dumps the log to the background
class Log(object):
    LOG_SIZE = 4096  # We flush every 4 KiB

    # No log should be bigger than 1 GB
    MAX_LOG_SIZE = 1024 * 1024 * 1024 * 1

    def __init__(self, path, use_stdout=False):
        self.log = []
        self.log_size = 0

        self.lock = Lock()
        self.needs_flush = Condition(self.lock)
        self.last_rotation_time = time.time()
        self.use_stdout = use_stdout
        if not self.use_stdout:
            if path is None or not path:
                path = "."
            elif not os.path.exists(path):
                os.makedirs(path)
            self.filename = os.path.join(path,
                                         time.strftime("%Y-%m-%d-%H:%M:%S+0000-", time.gmtime()) + str(os.getpid()) +
                                         ".log")
        self.bytes_written = 0
        self.dumper = Thread(target=self.log_dumper)
        self.is_alive = True
        self.flush_immediately = False

        if not self.use_stdout:
            with open("current.log", "w") as log_file:
                log_file.write(self.filename)

        if ENABLE_LOGGING:
            self.dumper.start()

    def write(self, msg):
        if ENABLE_LOGGING:
            with self.lock:
                self.log.append(msg)
                self.log_size += len(msg)

                if self.log_size >= Log.LOG_SIZE or self.flush_immediately:
                    self.needs_flush.notify()

    def close(self):
        with self.lock:
            self.is_alive = False
            self.needs_flush.notify()

        self.dumper.join()

    def log_dumper(self):
        if self.use_stdout:
            output_dest = sys.stdout
        else:
            output_dest = open(self.filename, "a+")

        alive = True

        try:
            while alive:
                with self.lock:
                    alive = self.is_alive
                    while self.log_size < Log.LOG_SIZE and self.is_alive:
                        self.needs_flush.wait()
                        if self.flush_immediately:
                            break

                    oldlog = self.log
                    oldsize = self.log_size
                    self.log = []
                    self.log_size = 0

                for msg in oldlog:
                    output_dest.write(msg)

                self.bytes_written += oldsize

                if FLUSH_LOG or self.flush_immediately:
                    output_dest.flush()

                # Checks whether we've been dumping to this logfile for a while
                # and opens up a new file.
                now = time.time()

                if not self.use_stdout and \
                        (
                                now - self.last_rotation_time > LOG_ROTATION_INTERVAL or self.bytes_written > Log.MAX_LOG_SIZE):
                    self.last_rotation_time = now
                    self.filename = time.strftime("%Y-%m-%d-%H:%M:%S+0000-", time.gmtime()) + str(os.getpid()) + ".log"

                    output_dest.flush()
                    output_dest.close()

                    with open("current.log", "w") as current_log:
                        current_log.write(self.filename)

                    output_dest = open(self.filename, "a+")
                    self.bytes_written = 0

        finally:
            output_dest.flush()

            if output_dest != sys.stdout:
                output_dest.close()


_log = None


# Logging helper functions

def log_init(path, use_stdout):
    global _log
    print("initializing log")
    _log = Log(path, use_stdout)


# Cleanly closes the log and flushes all contents to disk.
def log_close():
    _log.close()


def set_log_name(name):
    global _hostname

    _hostname = '[' + name + ']'


def set_log_level(loglevel):
    global _log_level

    if isinstance(loglevel, int):
        _log_level = loglevel
    else:
        raise TypeError("Expects LogLevel Enum or int")


def should_log_level(log_level):
    return log_level >= _log_level


def set_immediate_flush(flush_immediately):
    global _log

    if not _log:
        raise ValueError("Logger is not initialized.")

    if not isinstance(flush_immediately, bool):
        raise TypeError("flush_immediately is expected of type bool but was {}".format(type(flush_immediately)))

    _log.flush_immediately = flush_immediately
    with _log.lock:
        _log.needs_flush.notify()


def log(level, msg):
    global _hostname
    if level < _log_level:
        return  # No logging if it's not a high enough priority message.

    log_time = datetime.utcnow()
    logtype = "{}  ".format(level.name)

    # loc is kept for debugging purposes. Uncomment the following line if you need to see the execution path.
    #    msg = loc + ": " + msg
    if _hostname == "[Unassigned]":
        # Print threadname for testing in multithreaded integration testing environments
        logmsg = "[{0}]: {1} [{2}]: {3}\n".format(
            threading.current_thread().name, logtype, log_time.strftime("%Y-%m-%d-%H:%M:%S+%f"), msg)
    else:
        logmsg = "{0}: {1} [{2}]: {3}\n".format(
            _hostname, logtype, log_time.strftime("%Y-%m-%d-%H:%M:%S+%f"), msg)

    # Store all error messages to be sent to the frontend
    if level > LogLevel.WARN:
        error_msgs.append(logmsg)

    if len(error_msgs) > MAX_ERR_QUEUE_SIZE:
        error_msgs.popleft()

    _log.write(logmsg)

    # Print out crash logs to the console for easy debugging.
    if DUMP_LOG or level == LogLevel.FATAL:
        sys.stdout.write(logmsg)


def debug(msg):
    log(LogLevel.DEBUG, msg)


def trace(msg):
    log(LogLevel.TRACE, msg)


def error(msg):
    log(LogLevel.ERROR, msg)


def fatal(msg):
    log(LogLevel.FATAL, msg)


def info(msg):
    log(LogLevel.INFO, msg)


def warn(msg):
    log(LogLevel.WARN, msg)


def statistics(msg):
    log(LogLevel.STATS, msg)
