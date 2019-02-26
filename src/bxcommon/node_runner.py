import json

from bxcommon.models.node_model import NodeModel
from bxcommon.network import network_event_loop_factory
from bxcommon.services import sdn_http_service
from bxcommon.utils import cli, model_loader
from bxcommon.utils import config, logger
from bxcommon.utils.class_json_encoder import ClassJsonEncoder


def run_node(process_id_file_path, opts, node_class):
    config.log_pid(process_id_file_path)
    config.init_logging(opts.log_path, opts.to_stdout)

    # update constants from cli
    cli.set_sdn_url()

    node_model = None
    if opts.node_id:
        # Test network, get pre-configured peers from the SDN.
        node_model = sdn_http_service.fetch_config(opts.node_id)

    cli.set_blockchain_networks_info(opts)
    cli.parse_blockchain_opts(opts, node_class.NODE_TYPE)
    cli.set_os_version(opts)

    if not node_model:
        opts.node_type = node_class.NODE_TYPE
        node_model = sdn_http_service.register_node(model_loader.load(NodeModel, opts.__dict__))

    # Add opts from SDN, but don't overwrite CLI args
    for key, val in node_model.__dict__.items():
        if opts.__dict__.get(key) is None:
            opts.__dict__[key] = val

    if not hasattr(opts, "outbound_peers"):
        opts.__dict__["outbound_peers"] = []

    logger.set_log_name(opts.node_id)
    if cli.get_args().log_level is not None:
        logger.set_log_level(cli.get_args().log_level)

    logger.set_immediate_flush(cli.get_args().log_flush_immediately)

    logger.info("Config loaded:\n {}".format(json.dumps(opts, indent=2, sort_keys=True, cls=ClassJsonEncoder)))

    node = node_class(opts)
    event_loop = network_event_loop_factory.create_event_loop(node)

    # Start main loop
    try:
        logger.debug("Running node")
        event_loop.run()
    finally:
        logger.fatal("Node run method returned. Closing log and exiting.")
        logger.log_close()
