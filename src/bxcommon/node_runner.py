import json

from bxcommon.network import network_event_loop_factory
from bxcommon.services import sdn_service
from bxcommon.utils import config, logger


def run_node(process_id_file_path, opts, node_class):
    config.log_pid(process_id_file_path)
    config.init_logging(opts.log_path, opts.to_stdout)

    res_opts = None
    if opts.node_id:
        # Test network, get pre-configured peers from the SDN.
        res_opts = sdn_service.fetch_config(opts.node_id)

    if not res_opts:
        res_opts = sdn_service.register_node(opts, node_class.node_type)

    res_opts["outbound_peers"] = sdn_service.fetch_outbound_peers(res_opts.get("node_id"))

    # Add opts from SDN, but don't overwrite CLI args
    for key, val in res_opts.items():
        if opts.__dict__.get(key) is None:
            opts.__dict__[key] = val

    logger.log_setmyname(opts.node_id)

    logger.debug("Config loaded:\n {}".format(json.dumps(opts.__dict__, indent=2, sort_keys=True)))

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
