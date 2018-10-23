import json
import time

from bxcommon.constants import BX_API_ROUTES
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.services import http_service
from bxcommon.utils import config, logger


# TODO port this to sockets soon and remove json serialization perf hit on the node.
def fetch_config(node_id):
    # Should only be used for test networks.
    node_url = BX_API_ROUTES["node"].format(node_id)
    opts = http_service.get_json(node_url)
    logger.debug("Retrieved config for id {0} : {1}".format(node_id, opts))

    return opts


def fetch_outbound_peers(node_id):
    node_url = BX_API_ROUTES["node_peers"].format(node_id)
    outbound_peers = http_service.get_json(node_url)
    logger.debug("Retrieved outbound peers for id {0} : {1}".format(node_id, outbound_peers))

    if not outbound_peers:
        logger.warn("This node has no outbound peers.")

    _blocking_resolve_peers(outbound_peers)

    return outbound_peers


def submit_sid_space_full_event(node_id):
    submit_node_event(node_id, {
        "type": "SID_SPACE_FULL"
    })


def submit_node_online_event(node_id):
    submit_node_event(node_id, {
        "type": "ONLINE"
    })


def submit_node_offline_event(node_id):
    submit_node_event(node_id, {
        "type": "OFFLINE"
    })


def submit_peer_connection_error_event(node_id, peer_ip, peer_port):
    submit_node_event(node_id, {
        "type": "PEER_CONN_ERR",
        "peer_ip": peer_ip,
        "peer_port": peer_port
    })


def submit_node_event(node_id, event):
    event["node_id"] = node_id
    event["timestamp"] = str(time.time())
    logger.debug("Submitting event for node {0} {1}".format(node_id, json.dumps(event)))
    url = BX_API_ROUTES["node_event"].format(node_id)
    http_service.post_json(url, event)


def register_node(opts, node_type):
    if not opts.external_ip or not opts.external_port:
        raise EnvironmentError("Specify external_ip and external_port.")

    # Let the SDN know who this is.
    # SDN determines peers and returns full config.
    node_config = http_service.post_json(BX_API_ROUTES["nodes"], {
        "node_type": node_type,
        "external_ip": opts.external_ip,
        "external_port": opts.external_port
    })

    logger.debug("Registered node. Response: {}".format(json.dumps(node_config)))

    if not node_config:
        raise EnvironmentError("Unable to register this node.")

    return node_config


def _blocking_resolve_peers(peers):
    if not peers:
        return

    for peer in peers:
        peer_ip = peer.get(OutboundPeerModel.ip)

        resolved_ip = config.blocking_resolve_ip(peer_ip)

        if peer_ip != resolved_ip:
            logger.debug("Resolved peer {0} to {1}".format(peer_ip, resolved_ip))
            peer[OutboundPeerModel.ip] = resolved_ip

    logger.debug("Resolved peers successfully.")
