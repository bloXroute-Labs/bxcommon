import logging
from logging import LogRecord
from typing import Type

from bxutils.logging.log_level import LogLevel
from bxutils.logging_messages_utils import LogMessage

logger_class: Type[logging.Logger] = logging.getLoggerClass()
log_record_class: Type[LogRecord] = logging.getLogRecordFactory()  # pyre-ignore


# pyre-fixme[11]: Annotation `log_record_class` is not defined as a type.
class CustomLogRecord(log_record_class):

    def getMessage(self):

        msg = str(self.msg)
        if self.args:
            msg = msg.format(*self.args)
        return msg


# pyre-fixme[11]: Annotation `logger_class` is not defined as a type.
class CustomLogger(logger_class):

    def debug(self, msg, *args, **kwargs):
        self.log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.log(logging.ERROR, msg, *args, **kwargs)

    def exception(self, msg, *args, exc_info=True, **kwargs):
        self.log(logging.ERROR, msg, *args, exc_info=exc_info, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.log(logging.ERROR, msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        """
        Copied from logger class with a skipped type check.
        """
        if self.isEnabledFor(level):
            self._log(level, msg, args, **kwargs)

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
        if isinstance(msg, LogMessage):
            if extra is None:
                extra = {}
            extra["code"] = msg.code
            extra["category"] = msg.category
            msg = msg.text
        super(CustomLogger, self)._log(level, msg, args, exc_info, extra, stack_info)

    def fatal(self, msg, *args, exc_info=True, **kwargs):
        if self.isEnabledFor(LogLevel.FATAL):
            self.exception(msg, *args, exc_info=exc_info, **kwargs)

    def stats(self, msg, *args, **kwargs):
        if self.isEnabledFor(LogLevel.STATS):
            self._log(LogLevel.STATS, msg, args, kwargs)

    def statistics(self, msg, *args, **kwargs):
        self.stats(msg, *args, **kwargs)

    def trace(self, msg, *args, **kwargs):
        if self.isEnabledFor(LogLevel.TRACE):
            self._log(LogLevel.TRACE, msg, args, kwargs)

    def set_level(self, level):
        self.setLevel(level)

    def set_immediate_flush(self, flush_immediately: bool):
        pass
