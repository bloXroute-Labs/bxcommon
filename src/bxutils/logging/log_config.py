import logging
import os
import sys
import time
from asyncio import AbstractEventLoop
from logging import StreamHandler, FileHandler
from typing import Optional, List, Dict, Union, Iterable

from bxutils import constants
from bxutils import log_messages
from bxutils.logging.formatters import JSONFormatter, CustomFormatter, FluentJSONFormatter, AbstractFormatter
from bxutils.logging import log_level, LoggerConfig
from bxutils.logging.handler_type import HandlerType
from bxutils.logging.log_format import LogFormat
from bxutils.logging.log_level import LogLevel
from bxutils.encoding.json_encoder import EnhancedJSONEncoder

try:
    # TODO: remove try catch clause once the dependencies are installed
    import msgpack
    from aiofluent.handler import FluentHandler
    from bxutils.logging.fluentd_logging_helpers import overflow_handler
except ImportError:
    FluentHandler = None
    fluentd_logging_helpers = None
    overflow_handler = None

logger = logging.getLogger(__name__)


def _get_handler_file(folder_path: str) -> FileHandler:
    assert folder_path is not None, "log folder path is missing"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filename = os.path.join(
        folder_path,
        "{}{}.log".format(time.strftime("%Y-%m-%d-%H:%M:%S+0000-", time.gmtime()), str(os.getpid()))
    )
    return FileHandler(filename)


def _get_handler_fluentd(fluentd_host: Optional[str],
                         fluentd_tag_suffix: Optional[str],
                         max_queue_size: int,
                         loop: Optional[AbstractEventLoop] = None):
    assert fluentd_host is not None, "fluentd host name is missing"
    assert FluentHandler is not None, "fluentd handler is not installed"

    if ":" in fluentd_host:
        fluentd_host, fluentd_port = fluentd_host.split(":")
    else:
        fluentd_port = constants.FLUENTD_PORT
    if fluentd_tag_suffix:
        fluentd_tag = constants.FLUENTD_DEFAULT_TAG + "." + fluentd_tag_suffix
    else:
        fluentd_tag = constants.FLUENTD_DEFAULT_TAG
    return FluentHandler(
        fluentd_tag,
        host=fluentd_host,
        port=int(fluentd_port),
        buffer_overflow_handler=overflow_handler,
        nanosecond_precision=True,
        max_queue_size=max_queue_size,
        log_unhandled_exceptions=True,
        loop=loop,
        packer_kwargs={"default": EnhancedJSONEncoder().default}
    )


def _get_formatter(log_format: LogFormat, root_log_level: LogLevel, style: str, handler_type: HandlerType):
    if log_format == LogFormat.PLAIN:
        if root_log_level <= LogLevel.DEBUG:
            formatter = CustomFormatter(fmt=constants.DEBUG_LOG_FORMAT_PATTERN,
                                        datefmt=constants.PLAIN_LOG_DATE_FORMAT_PATTERN,
                                        style=style)
        else:
            formatter = CustomFormatter(fmt=constants.INFO_LOG_FORMAT_PATTERN,
                                        datefmt=constants.PLAIN_LOG_DATE_FORMAT_PATTERN,
                                        style=style)
    elif handler_type == HandlerType.Fluent:
        formatter = FluentJSONFormatter(style=style)
    elif log_format == LogFormat.JSON:
        formatter = JSONFormatter(style=style)
    else:
        raise ValueError("LOG_FORMAT was not set correctly: {}".format(log_format))
    return formatter


def create_logger(
        global_logger_name: Optional[str],
        root_log_level: LogLevel = constants.DEFAULT_LOG_LEVEL,
        log_format: LogFormat = constants.DEFAULT_LOG_FORMAT,
        handler_type: HandlerType = HandlerType.Stream,
        flush_handlers: bool = True,
        folder_path: Optional[str] = None,
        style: str = "{",
        fluentd_host: Optional[str] = None,
        fluentd_tag_suffix: Optional[str] = None,
        max_queue_size=constants.FLUENTD_LOGGER_MAX_QUEUE_SIZE,
        handler_log_level: Optional[LogLevel] = None,
        loop: Optional[AbstractEventLoop] = None
) -> None:
    """
    Installs a log configuration under the provided name.
    :param global_logger_name: log configuration name; None sets root logger
    :param root_log_level: the log level
    :param log_format: the logger format
    :param folder_path: optional file path (if specified - will write to the logs to files instead stdout)
    :param handler_type: enum log handler type
    :param flush_handlers: bool reset logging handlers
    :param style: the logger formatting style
    :param fluentd_host: fluentd host for fluent log handler
    :param fluentd_tag_suffix: optional fluentd tag suffix
    :param max_queue_size: the maximum size of the fluent logger queue
    :param handler_log_level: a specific log level for the handler itself (optional)
    :param loop: event loop optional, used in the fluentd handler
    """
    formatter = _get_formatter(log_format, root_log_level, style, handler_type)

    custom_logger = logging.getLogger(global_logger_name)

    if handler_type == HandlerType.File:
        assert folder_path is not None
        handler = _get_handler_file(folder_path)
    elif handler_type == HandlerType.Fluent:
        handler = _get_handler_fluentd(fluentd_host, fluentd_tag_suffix, max_queue_size, loop)
    else:
        handler = StreamHandler(sys.stdout)

    handler.setFormatter(formatter)
    if handler_log_level is not None:
        handler.setLevel(handler_log_level)

    custom_logger.propagate = False
    if custom_logger.hasHandlers() and flush_handlers:
        custom_logger.handlers = []
    custom_logger.addHandler(handler)
    custom_logger.setLevel(root_log_level)


def set_level(logger_names: List[Optional[str]], level: LogLevel) -> None:
    for logger_name in logger_names:
        logging.getLogger(logger_name).setLevel(level)


def set_log_levels(log_config: Dict[str, Union[LogLevel, str]]):
    # pyre-fixme[16]: `RootLogger` has no attribute `manager`.
    all_loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]

    for logger_instance in all_loggers:
        for log_name, custom_log_level in log_config.items():
            if logger_instance.name.endswith(log_name):
                try:
                    if isinstance(custom_log_level, str):
                        custom_log_level = log_level.from_string(custom_log_level)
                    logging.getLogger(logger_instance.name).setLevel(custom_log_level)
                except (KeyError, AttributeError):
                    logger.error(log_messages.INVALID_LOG_LEVEL, log_name, custom_log_level)


def lazy_set_log_level(log_overrides) -> None:
    log_configs = {}
    for stats_logger_name in constants.STATS_LOGGER_NAMES:
        log_configs[stats_logger_name] = constants.DEFAULT_STATS_LOG_LEVEL
    log_configs.update(log_overrides)
    set_log_levels(log_configs)


def set_instance(instance: str) -> None:
    # TODO: change function signature
    AbstractFormatter.instance = instance


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
        fluentd_queue_size: int = constants.FLUENTD_LOGGER_MAX_QUEUE_SIZE,
        fluentd_tag_suffix: Optional[str] = None,
        third_party_loggers: Optional[List[LoggerConfig]] = None,
        fluent_log_level: Optional[LogLevel] = None,
        stdout_log_level: Optional[LogLevel] = None,
        loop: Optional[AbstractEventLoop] = None
        ) -> None:
    loggers_config = [LoggerConfig(None, root_log_style, root_log_level)]
    if third_party_loggers is not None:
        loggers_config.extend(third_party_loggers)

    for logger_config in loggers_config:
        if logger_config.log_handler_type is None or logger_config.log_handler_type == HandlerType.Stream:
            create_logger(
                logger_config.name,
                # pyre-fixme[6]: Expected `LogLevel` for 2nd param but got
                #  `Optional[LogLevel]`.
                root_log_level=logger_config.log_level if logger_config.log_level is not None else default_log_level,
                log_format=log_format,
                style=logger_config.style,
                handler_type=HandlerType.Stream,
                handler_log_level=stdout_log_level
            )
        if enable_fluent_logger and LoggerConfig.log_handler_type is None \
                or LoggerConfig.log_handler_type == HandlerType.Fluent:
            create_logger(
                logger_config.name,
                # pyre-fixme[6]: Expected `LogLevel` for 2nd param but got
                #  `Optional[LogLevel]`.
                root_log_level=logger_config.log_level if logger_config.log_level is not None else default_log_level,
                log_format=LogFormat.JSON,
                style=logger_config.style,
                handler_type=HandlerType.Fluent,
                flush_handlers=False,
                fluentd_host=fluentd_host,
                max_queue_size=fluentd_queue_size,
                fluentd_tag_suffix=fluentd_tag_suffix,
                handler_log_level=fluent_log_level,
                loop=loop
            )
        elif enable_fluent_logger:
            print("Cannot Init fluentd logger")
    log_level_config = {}
    for logger_name in default_logger_names:
        log_level_config[logger_name] = default_log_level

    for stats_logger_name in constants.STATS_LOGGER_NAMES:
        log_level_config[stats_logger_name] = constants.DEFAULT_STATS_LOG_LEVEL

    log_level_config.update(log_level_overrides)
    set_log_levels(log_level_config)
