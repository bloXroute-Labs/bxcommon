import os
from typing import Dict, Any
from logging import Formatter, LogRecord
import json
from datetime import datetime
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

EXCLUDE_FROM_PLAIN_FORMATTING = {
    "category"
}


class AbstractFormatter(Formatter):
    FORMATTERS = {
        "%": lambda msg, args: str(msg) % args,
        "{": lambda msg, args: str(msg).format(*args)
    }

    def __init__(self, fmt=None, datefmt=None, style="{") -> None:
        super().__init__(fmt=fmt, datefmt=datefmt)
        self._formatter = self.FORMATTERS[style]

    NO_INSTANCE: str = "[Unassigned]"
    instance: str = NO_INSTANCE

    def _handle_args(self, record) -> str:
        try:
            if record.args and isinstance(record.args[0], str) and record.args[0] == constants.HAS_PREFIX:
                prefix = record.args[1]
                r_args = record.args[2:]
                return " ".join([prefix, self._formatter(record.msg, r_args)])
        except KeyError:
            pass
        return self._formatter(record.msg, record.args)


class JSONFormatter(AbstractFormatter):

    def format(self, record):
        return json.dumps(self._format_json(record), cls=EnhancedJSONEncoder)

    def _format_json(self, record: LogRecord,) -> Dict[Any, Any]:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created),
            "level": record.levelname,
            "name": record.name,
            "pid": os.getpid()
        }
        log_record.update({k: v for k, v in record.__dict__.items() if k not in BUILT_IN_ATTRS})

        if record.args:
            # There has to be a better way to do this...
            log_record["msg"] = self._handle_args(record)
        else:
            log_record["msg"] = record.msg
        if record.exc_info:
            # pyre-fixme[6]: Expected `Union[Tuple[None, None, None],
            #  Tuple[typing.Type[typing.Any], BaseException,
            #  Optional[types.TracebackType]]]` for 1st param but got
            #  `Optional[typing.Union[Tuple[None, None, None],
            #  Tuple[typing.Type[typing.Any], BaseException,
            #  Optional[types.TracebackType]]]]`.
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
        log_record = {k: v for k, v in record.__dict__.items() if
                      k not in BUILT_IN_ATTRS and k not in EXCLUDE_FROM_PLAIN_FORMATTING}
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
        current_time = datetime.fromtimestamp(record.created)
        if datefmt:
            s = current_time.astimezone().strftime(datefmt)
        else:
            s = current_time.isoformat()
        return s
