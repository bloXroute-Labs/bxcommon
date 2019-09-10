import logging
import sys
import os
import time
from typing import Optional, List
from logging import StreamHandler, FileHandler

from bxutils import constants
from bxutils.logging.log_format import LogFormat, JSONFormatter, CustomFormatter
from bxutils.logging.log_level import LogLevel


def create_logger(
        global_logger_name: Optional[str],
        log_level: int = constants.DEFAULT_LOG_LEVEL,
        log_format: LogFormat = constants.DEFAULT_LOG_FORMAT,
        folder_path: Optional[str] = None
) -> None:
    """
    Installs a log configuration under the provided name.
    :param global_logger_name: log configuration name; None sets root logger
    :param log_level: the log level
    :param log_format: the logger format
    :param folder_path: optional file path (if specified - will write to the logs to files instead stdout)
    """
    if log_format == LogFormat.PLAIN:
        formatter = CustomFormatter(fmt=constants.LOG_FORMAT_PATTERN)
    elif log_format == LogFormat.JSON:
        formatter = JSONFormatter()
    else:
        raise ValueError("LOG_FORMAT was not set correctly: {}".format(log_format))

    logger = logging.getLogger(global_logger_name)
    if folder_path is None:
        handler = StreamHandler(sys.stdout)
    else:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        filename = os.path.join(
            folder_path,
            "{}{}.log".format(time.strftime("%Y-%m-%d-%H:%M:%S+0000-", time.gmtime()), str(os.getpid()))
        )
        handler = FileHandler(filename)
    handler.setFormatter(formatter)
    logger.propagate = False
    if logger.hasHandlers():
        logger.handlers = []
    logger.addHandler(handler)
    logger.setLevel(log_level)


def set_level(logger_names: List[Optional[str]], level: LogLevel) -> None:
    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)


def set_instance(logger_names: List[Optional[str]], instance: str):
    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers:
            formatter = handler.formatter
            if hasattr(formatter, "instance"):
                formatter.instance = instance
