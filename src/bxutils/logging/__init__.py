import logging
import typing

from bxutils.logging.log_record_type import LogRecordType
from bxutils.logging.log_level import LogLevel
from typing import Optional, Union, NamedTuple

from bxutils.logging.custom_logger import CustomLogger, CustomLogRecord

logging.setLogRecordFactory(CustomLogRecord)  # pyre-ignore
logging.setLoggerClass(CustomLogger)


class LoggerConfig(NamedTuple):
    name: Optional[str]
    style: str
    log_level: Optional[LogLevel]


def get_logger(name: Optional[Union[str, LogRecordType]] = None,
               parent_class_name: Optional[str] = None) -> CustomLogger:
    """
    Return a logger with the specified name, creating it if necessary.

    :param name: Name of the logger
    :param parent_class_name: The name of the class the logger is in
    :return: The logger
    """
    if isinstance(name, LogRecordType):
        name = name.value

    if parent_class_name:
        name = "{}.{}".format(parent_class_name, name)

    return typing.cast(CustomLogger, logging.getLogger(name))
