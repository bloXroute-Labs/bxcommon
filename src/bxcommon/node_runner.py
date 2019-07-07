from bxcommon.models.node_model import NodeModel
from bxcommon.network import network_event_loop_factory
from bxcommon.services import sdn_http_service
from bxcommon.utils import cli, model_loader
from bxcommon.utils import config, logger
from bxcommon.exceptions import TerminationError


def run_node(process_id_file_path, opts, node_class, node_type=None):
    if node_type is None:
        node_type = node_class.NODE_TYPE

    config.log_pid(process_id_file_path)
    config.init_logging(opts.log_path, opts.to_stdout)
    try:
        if opts.use_extensions:
            from bxcommon.utils.proxy import task_pool_proxy
            task_pool_proxy.init(opts.thread_pool_parallelism_degree)
            logger.info(
                "initialized task thread pool parallelism degree to "
                f"{task_pool_proxy.get_pool_size()}."
            )
        _run_node(opts, node_class, node_type)
    except TerminationError:
        logger.fatal("Node terminated")
    except Exception as e:
        logger.fatal("Unhandled exception %s raised, terminating!", e)
    finally:
        logger.log_close()


def _run_node(opts, node_class, node_type):
    # update constants from cli
    cli.set_sdn_url()

    node_model = None
    if opts.node_id:
        # Test network, get pre-configured peers from the SDN.
        node_model = sdn_http_service.fetch_node_attributes(opts.node_id)

    cli.set_blockchain_networks_info(opts)
    cli.parse_blockchain_opts(opts, node_type)
    cli.set_os_version(opts)

    if not node_model:
        opts.node_type = node_type
        node_model = sdn_http_service.register_node(model_loader.load_model(NodeModel, opts.__dict__))

    # Add opts from SDN, but don't overwrite CLI args
    for key, val in node_model.__dict__.items():
        if opts.__dict__.get(key) is None:
            opts.__dict__[key] = val

    if not hasattr(opts, "outbound_peers"):
        opts.__dict__["outbound_peers"] = []

    logger.set_log_name(opts.node_id)
    if cli.get_args().log_level is not None:
        logger.set_log_level(cli.get_args().log_level)
    if cli.get_args().log_format is not None:
        logger.set_log_format(cli.get_args().log_format)

    logger.set_immediate_flush(cli.get_args().log_flush_immediately)

    logger.info({"type": "node_init", "Data": opts})

    # Start main loop
    node = node_class(opts)
    event_loop = network_event_loop_factory.create_event_loop(node)

    logger.debug("Running node")
    event_loop.run()
