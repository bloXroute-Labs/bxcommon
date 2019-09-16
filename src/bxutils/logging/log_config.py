import logging
import sys
import os
import time
from typing import Optional, List, Dict, Union
from logging import StreamHandler, FileHandler

from bxutils import constants
from bxutils.logging.log_format import LogFormat, JSONFormatter, CustomFormatter
from bxutils.logging.log_level import LogLevel

from bxutils.logging import log_level

logger = logging.getLogger(__name__)


def create_logger(
        global_logger_name: Optional[str],
        log_level: int = constants.DEFAULT_LOG_LEVEL,
        log_format: LogFormat = constants.DEFAULT_LOG_FORMAT,
        folder_path: Optional[str] = None,
        style: str = "{"
) -> None:
    """
    Installs a log configuration under the provided name.
    :param global_logger_name: log configuration name; None sets root logger
    :param log_level: the log level
    :param log_format: the logger format
    :param folder_path: optional file path (if specified - will write to the logs to files instead stdout)
    :param style: the logger formatting style
    """
    if log_format == LogFormat.PLAIN:
        formatter = CustomFormatter(fmt=constants.LOG_FORMAT_PATTERN, style=style)
    elif log_format == LogFormat.JSON:
        formatter = JSONFormatter(style=style)
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
        logging.getLogger(logger_name).setLevel(level)


def set_log_levels(log_config: Dict[str, Union[LogLevel, str]]):
    for log_name, custom_log_level in log_config.items():
        try:
            if isinstance(custom_log_level, str):
                custom_log_level = log_level.from_string(custom_log_level)
            logging.getLogger(log_name).setLevel(custom_log_level)
        except (KeyError, AttributeError):
            logger.error("Invalid Log Level Provided Ignore for path {}: {}", log_name, custom_log_level)


def set_instance(logger_names: List[Optional[str]], instance: str):
    logger_names.append(None)  # make sure we also set the instance on the root logger
    for logger_name in logger_names:
        custom_logger = logging.getLogger(logger_name)
        for handler in custom_logger.handlers:
            formatter = handler.formatter
            if hasattr(formatter, "instance"):
                formatter.instance = instance


def str_to_log_options(value: str) -> Dict[str, LogLevel]:
    d = {}
    pairs = value.split(",")
    for pair in pairs:
        name, level = pair.split("=", 1)
        d[name] = log_level.from_string(level)
    return d


def setup_logging(
        log_format: LogFormat,
        default_log_level: LogLevel,
        default_logger_names: List[str],
        log_level_overrides: Dict[str, LogLevel],
        root_log_level: LogLevel = LogLevel.WARNING,
        root_log_style: str = "{"):
    create_logger(None, log_level=root_log_level, log_format=log_format, style=root_log_style)
    log_level_config = {}
    for logger_name in default_logger_names:
        log_level_config[logger_name] = default_log_level
    log_level_config.update(log_level_overrides)
    set_log_levels(log_level_config)


