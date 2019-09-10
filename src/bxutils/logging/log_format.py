# An enum that stores the different log levels
from enum import Enum
from logging import Formatter
import json
from datetime import datetime
from bxutils.encoding.json_encoder import EnhancedJSONEncoder


BUILT_IN_ATTRS = {
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
    NO_INSTANCE: str = "[Unassigned]"
    instance: str = NO_INSTANCE


class JSONFormatter(AbstractFormatter):

    def format(self, record) -> str:
        log_record = {k: v for k, v in record.__dict__.items() if k not in BUILT_IN_ATTRS}
        if record.args:
            log_record["msg"] = str(record.msg).format(*record.args)
        else:
            log_record["msg"] = record.msg
        if "timestamp" not in log_record:
            log_record["timestamp"] = datetime.utcnow()
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        log_record["level"] = record.levelname
        log_record["name"] = record.name
        if self.instance != self.NO_INSTANCE:
            log_record["instance"] = self.instance
        return json.dumps(log_record, cls=EnhancedJSONEncoder)


class CustomFormatter(AbstractFormatter):
    encoder = EnhancedJSONEncoder()

    def format(self, record) -> str:
        log_record = {k: v for k, v in record.__dict__.items() if k not in BUILT_IN_ATTRS}
        if record.args and not hasattr(record.msg, "__dict__"):
            log_record["msg"] = str(record.msg).format(*record.args)
        else:
            log_record["msg"] = record.msg
        if self.instance != self.NO_INSTANCE:
            log_record["instance"] = self.instance
        record.msg = "{}{}".format(self.encoder.encode(record.msg),
                                   ",".join({" {}={}".format(k, self.encoder.encode(v)) for (k, v)
                                             in log_record.items() if k != "msg"}))
        return super(CustomFormatter, self).format(record)

    def formatTime(self, record, datefmt=None) -> str:
        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            s = ct.isoformat()
        return s
