import logging
import sys
import os
import time

from typing import Optional, List, Dict, Union, Iterable
from logging import StreamHandler, FileHandler

from bxutils import constants
from bxutils.logging.log_format import LogFormat, JSONFormatter, CustomFormatter, FluentJSONFormatter
from bxutils.logging.log_level import LogLevel
from bxutils.logging.handler_type import HandlerType
from bxutils.logging import log_level, LoggerConfig

try:
    # TODO: remove try catch clause once the decencies are installed
    import msgpack
    from fluent.asynchandler import FluentHandler
    from bxutils.logging.fluentd_logging_helpers import overflow_handler
except ImportError:
    FluentHandler = None
    fluentd_logging_helpers = None
    overflow_handler = None

logger = logging.getLogger(__name__)


def create_logger(
        global_logger_name: Optional[str],
        log_level: int = constants.DEFAULT_LOG_LEVEL,
        log_format: LogFormat = constants.DEFAULT_LOG_FORMAT,
        handler_type: HandlerType = HandlerType.Stream,
        flush_handlers: bool = True,
        folder_path: Optional[str] = None,
        style: str = "{",
        fluentd_host: Optional[str] = None,
        fluentd_tag_suffix: Optional[str] = None
) -> None:
    """
    Installs a log configuration under the provided name.
    :param global_logger_name: log configuration name; None sets root logger
    :param log_level: the log level
    :param log_format: the logger format
    :param folder_path: optional file path (if specified - will write to the logs to files instead stdout)
    :param handler_type: enum log handler type
    :param flush_handlers: bool reset logging handlers
    :param style: the logger formatting style
    :param fluentd_host: fluentd host for fluent log handler
    :param fluentd_tag_suffix: optional fluentd tag suffix
    """
    if log_format == LogFormat.PLAIN:
        if log_level <= LogLevel.DEBUG:
            formatter = CustomFormatter(fmt=constants.DEBUG_LOG_FORMAT_PATTERN, style=style)
        else:
            formatter = CustomFormatter(fmt=constants.INFO_LOG_FORMAT_PATTERN, style=style)
    elif handler_type == HandlerType.Fluent:
        formatter = FluentJSONFormatter(style=style)
    elif log_format == LogFormat.JSON:
        formatter = JSONFormatter(style=style)
    else:
        raise ValueError("LOG_FORMAT was not set correctly: {}".format(log_format))

    logger = logging.getLogger(global_logger_name)

    if handler_type == HandlerType.File:
        assert folder_path is not None, "log folder path is missing"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        filename = os.path.join(
            folder_path,
            "{}{}.log".format(time.strftime("%Y-%m-%d-%H:%M:%S+0000-", time.gmtime()), str(os.getpid()))
        )
        handler = FileHandler(filename)
    elif handler_type == HandlerType.Fluent:
        assert fluentd_host is not None, "fluentd host name is missing"
        if ":" in fluentd_host:
            fluent_host, fluentd_port = fluentd_host.split(":")
        else:
            fluentd_port = constants.FLUENTD_PORT
        if fluentd_tag_suffix:
            fluentd_tag = constants.FLUENTD_DEFAULT_TAG + "." + fluentd_tag_suffix
        else:
            fluentd_tag = constants.FLUENTD_DEFAULT_TAG
        handler = FluentHandler(
            fluentd_tag,
            host=fluentd_host,
            port=fluentd_port,
            buffer_overflow_handler=overflow_handler,
            nanosecond_precision=True
        )
    else:
        handler = StreamHandler(sys.stdout)

    handler.setFormatter(formatter)
    logger.propagate = False
    if logger.hasHandlers() and flush_handlers:
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
        default_logger_names: Iterable[str],
        log_level_overrides: Dict[str, LogLevel],
        root_log_level: LogLevel = LogLevel.WARNING,
        root_log_style: str = "{",
        enable_fluent_logger: bool = False,
        fluentd_host: Optional[str] = None,
        fluentd_tag_suffix: Optional[str] = None,
        third_party_loggers: Optional[List[LoggerConfig]] = None
        ):
    loggers_config = [LoggerConfig(None, root_log_style, root_log_level)]
    if third_party_loggers is not None:
        loggers_config.extend(third_party_loggers)

    for logger_config in loggers_config:
        create_logger(
            logger_config.name,
            log_level=logger_config.log_level if logger_config.log_level is not None else default_log_level,
            log_format=log_format,
            style=logger_config.style,
            handler_type=HandlerType.Stream
        )
        if enable_fluent_logger and fluentd_host is not None and FluentHandler is not None:
            create_logger(logger_config.name,
                          log_level=logger_config.log_level if logger_config.log_level is not None else default_log_level,
                          log_format=LogFormat.JSON,
                          style=logger_config.style,
                          handler_type=HandlerType.Fluent,
                          flush_handlers=False,
                          fluentd_host=fluentd_host,
                          fluentd_tag_suffix=fluentd_tag_suffix)
        elif enable_fluent_logger:
            print("Cannot Init fluentd logger")
    log_level_config = {}
    for logger_name in default_logger_names:
        log_level_config[logger_name] = default_log_level
    log_level_config.update(log_level_overrides)
    set_log_levels(log_level_config)
