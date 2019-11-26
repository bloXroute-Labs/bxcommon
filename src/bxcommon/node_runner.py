import sys

from datetime import datetime
from typing import List, Optional

from bxutils import logging
from bxutils.logging import log_config

from bxcommon.models.node_model import NodeModel
from bxcommon.network import network_event_loop_factory
from bxcommon.services import sdn_http_service
from bxcommon.utils import cli, model_loader
from bxcommon.utils import config
from bxcommon.exceptions import TerminationError
from bxutils.logging.status import status_log

logger = logging.get_logger(__name__)

LOGGER_NAMES = ["bxcommon", "bxutils", "stats", "bx"]


def run_node(process_id_file_path, opts, node_class, node_type=None, logger_names: List[Optional[str]] = LOGGER_NAMES):
    opts.logger_names = logger_names
    log_config.setup_logging(opts.log_format,
                             opts.log_level,
                             logger_names,
                             opts.log_level_overrides,
                             enable_fluent_logger=opts.log_fluentd_enable,
                             fluentd_host=opts.log_fluentd_host)
    startup_param = sys.argv[1:]
    logger.info("Startup Parameters are: {}", " ".join(startup_param))
    status_log.initialize(opts.use_extensions, opts.source_version)

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
        _run_node(opts, node_class, node_type, logger_names)
    except TerminationError:
        logger.fatal("Node terminated")
    except Exception as e:
        logger.fatal("Unhandled exception {} raised, terminating!", e)
    for handler in logger.handlers:
        if hasattr(handler, "close"):
            handler.close()


def _run_node(opts, node_class, node_type, logger_names: List[Optional[str]]):
    node_model = None
    if opts.node_id:
        # Test network, get pre-configured peers from the SDN.
        node_model = sdn_http_service.fetch_node_attributes(opts.node_id)

    cli.set_blockchain_networks_info(opts)
    cli.parse_blockchain_opts(opts, node_type)
    cli.set_os_version(opts)

    opts.node_start_time = datetime.utcnow()
    if not node_model:
        opts.node_type = node_type
        node_model = sdn_http_service.register_node(model_loader.load_model(NodeModel, opts.__dict__))

    # Add opts from SDN, but don't overwrite CLI args
    for key, val in node_model.__dict__.items():
        if opts.__dict__.get(key) is None:
            opts.__dict__[key] = val

    if not hasattr(opts, "outbound_peers"):
        opts.__dict__["outbound_peers"] = []

    logger.debug({"type": "node_init", "Data": opts})

    # Start main loop
    node = node_class(opts)
    log_config.set_instance(logger_names, node.opts.node_id)
    event_loop = network_event_loop_factory.create_event_loop(node)

    logger.trace("Running node...")
    event_loop.run()
