import asyncio
import gc
import sys
import os

from typing import Iterable, Optional, Type, Callable, List

import uvloop

from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.exceptions import TerminationError, HighMemoryError, FeedSubscriptionTimeoutError
from bxcommon.models.node_type import NodeType
from bxcommon.network.node_event_loop import NodeEventLoop
from bxcommon.services import sdn_http_service
from bxcommon.utils import config
from bxcommon.common_opts import CommonOpts
from bxcommon import common_init_tasks
from bxutils import log_messages
from bxutils import logging
from bxutils.logging import log_config, LoggerConfig, gc_logger
from bxutils.logging.log_level import LogLevel
from bxutils.services.node_ssl_service import NodeSSLService
from bxutils.ssl.data import ssl_data_factory
from bxutils.ssl.ssl_certificate_type import SSLCertificateType

InitTaskType = Callable[[CommonOpts, NodeSSLService], None]
OptsType = CommonOpts
logger = logging.get_logger(__name__)

LOGGER_NAMES = ["bxcommon", "bxutils"]
THIRD_PARTY_LOGGERS = [
    LoggerConfig("urllib3", "%", LogLevel.WARNING),
    LoggerConfig("asyncio", "%", LogLevel.ERROR),
]

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # pyre-ignore
asyncio.set_event_loop(uvloop.new_event_loop())


def default_ssl_service_factory(
    node_type: NodeType, ca_cert_url: str, private_ssl_base_url: str, data_dir: str
) -> NodeSSLService:
    storage_info = ssl_data_factory.create_storage_info(
        node_type=node_type,
        ca_cert_url=ca_cert_url,
        private_ssl_base_url=private_ssl_base_url,
        data_dir=data_dir,
    )
    return NodeSSLService(node_type, storage_info)


def run_node(
    process_id_file_path: str,
    opts: OptsType,
    get_node_class: Callable[[], Type[AbstractNode]],
    node_type: NodeType,
    logger_names: Optional[Iterable[str]] = tuple(LOGGER_NAMES),
    ssl_service_factory: Callable[
        [NodeType, str, str, str], NodeSSLService
    ] = default_ssl_service_factory,
    third_party_loggers: Optional[List[LoggerConfig]] = None,
    node_init_tasks: Optional[List[InitTaskType]] = None,
) -> None:

    if third_party_loggers is None:
        third_party_loggers = THIRD_PARTY_LOGGERS
    opts.logger_names = logger_names
    log_config.setup_logging(
        opts.log_format,
        opts.log_level,
        # pyre-fixme[6]: Expected `Iterable[str]` for 3rd param but got
        #  `Iterable[Optional[str]]`.
        logger_names,
        opts.log_level_overrides,
        enable_fluent_logger=opts.log_fluentd_enable,
        fluentd_host=opts.log_fluentd_host,
        fluentd_queue_size=opts.log_fluentd_queue_size,
        third_party_loggers=third_party_loggers,
        fluent_log_level=opts.log_level_fluentd,
        stdout_log_level=opts.log_level_stdout,
        fluentd_tag_suffix=node_type.name.lower()
    )
    if node_init_tasks is None:
        node_init_tasks = common_init_tasks.init_tasks

    startup_param = sys.argv[1:]
    logger.info("Startup Parameters are: {}", " ".join(startup_param))

    _verify_environment()

    config.log_pid(process_id_file_path)
    gc.callbacks.append(gc_logger.gc_callback)
    # we disable GC generation cleanup.
    # use gc.collect() if memory exceeds threshold
    gc.disable()
    try:
        if opts.use_extensions:
            from bxcommon.utils.proxy import task_pool_proxy

            task_pool_proxy.init(opts.thread_pool_parallelism_degree)
            logger.debug(
                "Initialized task thread pool parallelism degree to {}.",
                task_pool_proxy.get_pool_size(),
            )

        _run_node(
            opts,
            get_node_class,
            node_type,
            node_init_tasks=node_init_tasks,
            ssl_service_factory=ssl_service_factory,
        )
    except TerminationError:
        logger.fatal("Node terminated")
    except HighMemoryError:
        logger.info("Restarting node due to high memory")
        _close_handles()
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except FeedSubscriptionTimeoutError:
        logger.info(
            "Restarting node due to feed subscription timeout, "
            "node is probably not synced with the blockchain node."
        )
        _close_handles()
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as e:  # pylint: disable=broad-except
        logger.fatal("Unhandled exception {} raised, terminating!", e)

    _close_handles()


def _close_handles() -> None:
    for handler in logger.handlers:
        if hasattr(handler, "close"):
            handler.close()


def _run_node(
    opts: OptsType,
    get_node_class,
    node_type,
    node_init_tasks: List[InitTaskType],
    ssl_service_factory: Callable[
        [NodeType, str, str, str], NodeSSLService
    ] = default_ssl_service_factory,
) -> None:

    opts.node_type = node_type
    node_ssl_service = _init_ssl_service(
        node_type,
        opts.ca_cert_url,
        opts.private_ssl_base_url,
        opts.data_dir,
        ssl_service_factory=ssl_service_factory,
    )

    for task in node_init_tasks:
        task(opts, node_ssl_service)

    if not hasattr(opts, "outbound_peers"):
        opts.__dict__["outbound_peers"] = []

    logger.debug({"type": "node_init", "data": opts})

    # Start main loop
    node = get_node_class()(opts, node_ssl_service)
    log_config.set_instance(node.opts.node_id)
    loop = asyncio.get_event_loop()
    node_event_loop = NodeEventLoop(node)

    logger.trace("Running node...")
    loop.run_until_complete(node_event_loop.run())


def _init_ssl_service(
    node_type: NodeType,
    ca_cert_url: str,
    private_ssl_base_url: str,
    data_dir: str,
    ssl_service_factory: Callable[
        [NodeType, str, str, str], NodeSSLService
    ] = default_ssl_service_factory,
) -> NodeSSLService:
    node_ssl_service = ssl_service_factory(
        node_type, ca_cert_url, private_ssl_base_url, data_dir
    )
    node_ssl_service.blocking_load()

    if node_ssl_service.has_valid_certificate(SSLCertificateType.PRIVATE) \
        and not node_ssl_service.should_renew_node_certificate():
        ssl_context = node_ssl_service.create_ssl_context(SSLCertificateType.PRIVATE)
    else:
        ssl_context = node_ssl_service.create_ssl_context(
            SSLCertificateType.REGISTRATION_ONLY
        )

    sdn_http_service.reset_pool(ssl_context)
    return node_ssl_service


def _verify_environment() -> None:
    if sys.version.startswith("3.6."):
        logger.warning(log_messages.DETECTED_PYTHON3_6)
