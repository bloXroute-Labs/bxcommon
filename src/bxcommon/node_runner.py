import asyncio
import uvloop
import sys

from datetime import datetime
from typing import Iterable, Optional, Type, Union, Callable
from argparse import Namespace

from bxutils import logging
from bxutils.logging import log_config, LoggerConfig
from bxutils.logging.log_level import LogLevel
from bxutils.services.node_ssl_service import NodeSSLService
from bxutils.ssl.data import ssl_data_factory
from bxutils.ssl import ssl_serializer
from bxutils.ssl.ssl_certificate_type import SSLCertificateType

from bxcommon.utils.cli import CommonOpts
from bxcommon.models.node_type import NodeType
from bxcommon.models.node_model import NodeModel
from bxcommon.network.node_event_loop import NodeEventLoop
from bxcommon.services import sdn_http_service
from bxcommon.utils import cli, model_loader, config, node_cache
from bxcommon.exceptions import TerminationError
from bxcommon.connections.abstract_node import AbstractNode

logger = logging.get_logger(__name__)

LOGGER_NAMES = ["bxcommon", "bxutils"]
THIRD_PARTY_LOGGERS = [LoggerConfig("urllib3", "%", LogLevel.WARNING),
                       LoggerConfig("asyncio", "%", LogLevel.ERROR)]

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # pyre-ignore
asyncio.set_event_loop(uvloop.new_event_loop())


def default_ssl_service_factory(
        node_type: NodeType, ca_cert_url: str, private_ssl_base_url: str, data_dir: str
) -> NodeSSLService:
    storage_info = ssl_data_factory.create_storage_info(
        node_type=node_type,
        ca_cert_url=ca_cert_url,
        private_ssl_base_url=private_ssl_base_url,
        data_dir=data_dir
    )
    return NodeSSLService(node_type, storage_info)


def run_node(
        process_id_file_path: str,
        opts: Union[Namespace, CommonOpts],
        node_class: Type[AbstractNode],
        node_type: Optional[NodeType] = None,
        logger_names: Iterable[Optional[str]] = tuple(LOGGER_NAMES),
        ssl_service_factory: Callable[[NodeType, str, str, str], NodeSSLService] = default_ssl_service_factory
):
    opts.logger_names = logger_names
    log_config.setup_logging(opts.log_format,
                             opts.log_level,
                             logger_names,
                             opts.log_level_overrides,
                             enable_fluent_logger=opts.log_fluentd_enable,
                             fluentd_host=opts.log_fluentd_host,
                             third_party_loggers=THIRD_PARTY_LOGGERS)
    startup_param = sys.argv[1:]
    logger.info("Startup Parameters are: {}", " ".join(startup_param))

    _verify_environment()

    if node_type is None:
        node_type = node_class.NODE_TYPE

    config.log_pid(process_id_file_path)

    try:
        if opts.use_extensions:
            from bxcommon.utils.proxy import task_pool_proxy
            task_pool_proxy.init(opts.thread_pool_parallelism_degree)
            logger.debug(
                "Initialized task thread pool parallelism degree to {}.",
                task_pool_proxy.get_pool_size()
            )
        _run_node(opts, node_class, node_type, logger_names, ssl_service_factory=ssl_service_factory)
    except TerminationError:
        logger.fatal("Node terminated")
    except Exception as e:
        logger.fatal("Unhandled exception {} raised, terminating!", e)
    for handler in logger.handlers:
        if hasattr(handler, "close"):
            handler.close()


def _run_node(
        opts,
        node_class,
        node_type,
        logger_names: Iterable[Optional[str]],
        ssl_service_factory: Callable[[NodeType, str, str, str], NodeSSLService] = default_ssl_service_factory
):
    node_model = None
    if opts.node_id:
        # Test network, get pre-configured peers from the SDN.
        node_model = sdn_http_service.fetch_node_attributes(opts.node_id)

    node_ssl_service = _init_ssl_service(
        node_type, opts.ca_cert_url, opts.private_ssl_base_url, opts.data_dir, ssl_service_factory=ssl_service_factory
    )

    cli.set_blockchain_networks_info(opts)
    cli.parse_blockchain_opts(opts, node_type)
    cli.set_os_version(opts)

    opts.node_start_time = datetime.utcnow()
    if not node_model:
        opts.node_type = node_type

        temp_node_model = model_loader.load_model(NodeModel, opts.__dict__)
        if node_ssl_service.should_renew_node_certificate():
            temp_node_model.csr = ssl_serializer.serialize_csr(node_ssl_service.create_csr())

        try:
            node_model = sdn_http_service.register_node(temp_node_model)
        except ValueError as ve:
            logger.fatal(ve)
            exit(1)
        except EnvironmentError as e:
            logger.info("Unable to contact SDN to register node using {}, attempting to get information from cache",
                        opts.sdn_url)
            cache_info = node_cache.read(opts)
            if not cache_info or not cache_info.node_model:
                logger.fatal(
                    "Unable to reach the SDN and no local cache information was found. Unable to start the gateway")
                exit(1)
            node_model = cache_info.node_model

        if node_model.should_update_source_version:
            logger.info("UPDATE AVAILABLE! An updated software version is available, please download and install the "
                        "latest version")

        if node_model.cert is not None:
            private_cert = ssl_serializer.deserialize_cert(node_model.cert)
            node_ssl_service.blocking_store_node_certificate(private_cert)
            ssl_context = node_ssl_service.create_ssl_context(SSLCertificateType.PRIVATE)
            sdn_http_service.reset_pool(ssl_context)

    # Add opts from SDN, but don't overwrite CLI args
    for key, val in node_model.__dict__.items():
        if opts.__dict__.get(key) is None:
            opts.__dict__[key] = val

    if not hasattr(opts, "outbound_peers"):
        opts.__dict__["outbound_peers"] = []

    logger.debug({"type": "node_init", "data": opts})

    # Start main loop
    node = node_class(opts, node_ssl_service)
    log_config.set_instance(list(logger_names), node.opts.node_id)
    loop = asyncio.get_event_loop()
    node_event_loop = NodeEventLoop(node)

    logger.trace("Running node...")
    loop.run_until_complete(node_event_loop.run())


def _init_ssl_service(
        node_type: NodeType,
        ca_cert_url: str,
        private_ssl_base_url: str,
        data_dir: str,
        ssl_service_factory: Callable[[NodeType, str, str, str], NodeSSLService] = default_ssl_service_factory
) -> NodeSSLService:
    node_ssl_service = ssl_service_factory(node_type, ca_cert_url, private_ssl_base_url, data_dir)
    node_ssl_service.blocking_load()

    if node_ssl_service.has_valid_certificate(SSLCertificateType.PRIVATE):
        ssl_context = node_ssl_service.create_ssl_context(SSLCertificateType.PRIVATE)
    else:
        ssl_context = node_ssl_service.create_ssl_context(SSLCertificateType.REGISTRATION_ONLY)

    sdn_http_service.reset_pool(ssl_context)
    return node_ssl_service


def _verify_environment():
    if sys.version.startswith("3.6."):
        logger.warning("Python 3.6 environment is detected. Degraded performance is expected. "
                       "Upgrade to Python 3.7 or above for improved performance.")
