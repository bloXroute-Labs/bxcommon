# An enum that stores the different log levels
import os
from enum import Enum
from typing import Dict, Any
from logging import Formatter, LogRecord
import json
from datetime import datetime
from bxutils.encoding.json_encoder import EnhancedJSONEncoder

BUILT_IN_ATTRS = {
    "timestamp",
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


class LogFormat(Enum):
    JSON = "JSON"
    PLAIN = "PLAIN"

    def __str__(self):
        return self.name


class AbstractFormatter(Formatter):
    FORMATTERS = {
        "%": lambda msg, args: str(msg) % args,
        "{": lambda msg, args: str(msg).format(*args)
    }

    def __init__(self, fmt=None, datefmt=None, style="{"):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self._formatter = self.FORMATTERS[style]

    NO_INSTANCE: str = "[Unassigned]"
    instance: str = NO_INSTANCE


class JSONFormatter(AbstractFormatter):

    def format(self, record):  # pyre-ignore
        return json.dumps(self._format_json(record), cls=EnhancedJSONEncoder)

    def _format_json(self, record: LogRecord) -> Dict[Any, Any]:
        log_record = {"timestamp": record.__dict__.get("timestamp", datetime.utcnow()),
                      "level": record.levelname,
                      "name": record.name,
                      "pid": os.getpid()
                      }
        log_record.update({k: v for k, v in record.__dict__.items() if k not in BUILT_IN_ATTRS})

        if record.args:
            log_record["msg"] = self._formatter(record.msg, record.args)
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        if self.instance != self.NO_INSTANCE:
            log_record["instance"] = self.instance
        return log_record


class FluentJSONFormatter(JSONFormatter):
    # TODO: check if there is a correct way to annotate this
    def format(self, record):
        return EnhancedJSONEncoder().as_dict(self._format_json(record))


class CustomFormatter(AbstractFormatter):
    encoder = EnhancedJSONEncoder()

    def format(self, record) -> str:
        log_record = {k: v for k, v in record.__dict__.items() if k not in BUILT_IN_ATTRS}
        if record.args and not hasattr(record.msg, "__dict__"):
            record.msg = self._formatter(record.msg, record.args)
            record.args = ()

        record.msg = "{}{}".format(self.encoder.encode(record.msg),
                                   ",".join({" {}={}".format(k, self.encoder.encode(v)) for (k, v)
                                             in log_record.items() if k != "msg"}))
        if self.instance != self.NO_INSTANCE:
            record.instance = self.instance
        return super(CustomFormatter, self).format(record)

    def formatTime(self, record, datefmt=None) -> str:
        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            s = ct.astimezone().strftime(datefmt)
        else:
            s = ct.isoformat()
        return s
