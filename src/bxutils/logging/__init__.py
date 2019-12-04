import logging
import typing
from bxutils.logging.log_record_type import LogRecordType
from bxutils.logging.log_level import LogLevel
from typing import Optional, Union, NamedTuple

from bxutils.logging.custom_logger import CustomLogger, CustomLogRecord

logging.setLogRecordFactory(CustomLogRecord)  # pyre-ignore
logging.setLoggerClass(CustomLogger)


class ThirdPartyLoggers(NamedTuple):
    name: str
    style: str
    log_level: Optional[LogLevel]


def get_logger(name: Optional[Union[str, LogRecordType]] = None) -> CustomLogger:
    if isinstance(name, LogRecordType):
        name = name.value
    return typing.cast(CustomLogger, logging.getLogger(name))
