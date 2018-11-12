import json

from bxcommon.models.node_model import NodeModel
from bxcommon.network import network_event_loop_factory
from bxcommon.services import sdn_http_service
from bxcommon.utils import config, logger
from bxcommon.utils.class_json_encoder import ClassJsonEncoder


def run_node(process_id_file_path, opts, node_class):
    config.log_pid(process_id_file_path)
    config.init_logging(opts.log_path, opts.to_stdout)

    node_model = None
    if opts.node_id:
        # Test network, get pre-configured peers from the SDN.
        node_model = sdn_http_service.fetch_config(opts.node_id)

    if not node_model:
        node_model = sdn_http_service.register_node(
            NodeModel(node_type=node_class.node_type, external_ip=opts.external_ip, external_port=opts.external_port))

    # Add opts from SDN, but don't overwrite CLI args
    for key, val in node_model.__dict__.items():
        if opts.__dict__.get(key) is None:
            opts.__dict__[key] = val

    if not hasattr(opts, "outbound_peers"):
        opts.__dict__["outbound_peers"] = []

    logger.log_setmyname(opts.node_id)

    logger.debug("Config loaded:\n {}".format(json.dumps(opts, indent=2, sort_keys=True, cls=ClassJsonEncoder)))

    node = node_class(opts)
    event_loop = network_event_loop_factory.create_event_loop(node)

    # Start main loop
    try:
        logger.debug("Running node")
        event_loop.run()
    finally:
        logger.fatal("Node run method returned")
        logger.fatal("Log closed")
        logger.log_close()
