# An enum that stores the different log levels
import os
from enum import Enum
from typing import Dict, Any, Tuple
from logging import Formatter, LogRecord
import json
from datetime import datetime
from bxutils.logging_messages_utils import logger_names, LogMessage
from bxutils.log_message_categories import UNCATEGORIZED, THIRD_PARTY_CATEGORY
from bxutils.encoding.json_encoder import EnhancedJSONEncoder
from bxutils import constants

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

    def _handle_args(self, record):
        if isinstance(record.args[0], str) and record.args[0] == constants.HAS_PREFIX:
            prefix = record.args[1]
            r_args = record.args[2:]
            return " ".join([prefix, self._formatter(record.msg, r_args)])
        else:
            return self._formatter(record.msg, record.args)


class JSONFormatter(AbstractFormatter):

    def __init__(self, *args, **kwargs):
        super(JSONFormatter, self).__init__(args, kwargs)
        self.log_level_to_handler = dict.fromkeys(constants.CATEGORIZED_LOG_LEVELS,
                                                  self._handle_categorized_log_level)
        self.log_module_to_handler = dict.fromkeys(logger_names,
                                                   self._handle_categorized_log_name)

    def _handle_categorized_log_name(self, record: LogRecord) -> Tuple[str, str, str]:
        if record.msg.__class__.__name__ == "LogMessage":
            message_content = record.msg
        else:
            message_content = LogMessage("N/A", UNCATEGORIZED, record.msg)
        # pyre-ignore
        return message_content.code, message_content.category, message_content.text

    def _handle_categorized_log_level(self, record: LogRecord, log_record: Dict[Any, Any]):
        log_record["msg_code"], log_record["category"], record.msg = self.log_module_to_handler.get(
            record.name.split(".")[0],
            lambda x: (None, THIRD_PARTY_CATEGORY, record.msg)
        )(record)

    def _handle_record(self, record: LogRecord, log_record: Dict[Any, Any]):
        self.log_level_to_handler.get(
            record.levelname,
            (lambda x, y: (x, y))
        )(record, log_record)

    def format(self, record):  # pyre-ignore
        return json.dumps(self._format_json(record), cls=EnhancedJSONEncoder)

    def _format_json(self, record: LogRecord) -> Dict[Any, Any]:
        log_record = {"timestamp": record.__dict__.get("timestamp", datetime.utcnow()),
                      "level": record.levelname,
                      "name": record.name,
                      "pid": os.getpid()
                      }
        log_record.update({k: v for k, v in record.__dict__.items() if k not in BUILT_IN_ATTRS})

        self._handle_record(record, log_record)
        if record.args:
            # There has to be a better way to do this...
            log_record["msg"] = self._handle_args(record)
        else:
            log_record["msg"] = record.msg
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
            record.msg = self._handle_args(record)
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
