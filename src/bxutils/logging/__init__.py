import logging
import typing
from typing import Optional

from bxutils.logging.custom_logger import CustomLogger, CustomLogRecord

logging.setLogRecordFactory(CustomLogRecord)  # pyre-ignore
logging.setLoggerClass(CustomLogger)


def get_logger(name: Optional[str] = None) -> CustomLogger:
    return typing.cast(CustomLogger, logging.getLogger(name))
