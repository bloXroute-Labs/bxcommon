import logging
import typing
from dataclasses import dataclass
from typing import Optional, Union

from bxutils.logging.custom_logger import CustomLogger, CustomLogRecord
from bxutils.logging.handler_type import HandlerType
from bxutils.logging.log_level import LogLevel
from bxutils.logging.log_record_type import LogRecordType

logging.setLogRecordFactory(CustomLogRecord)  # pyre-ignore
logging.setLoggerClass(CustomLogger)


@dataclass()
class LoggerConfig:
    name: Optional[str]
    style: str
    log_level: Optional[LogLevel]
    log_handler_type: Optional[HandlerType] = None


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
