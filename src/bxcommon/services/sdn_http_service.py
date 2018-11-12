import json
import time

from bxcommon.constants import BxApiRoutes
from bxcommon.models.node_event_model import NodeEventModel, NodeEventType
from bxcommon.models.node_model import NodeModel
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.services import http_service
from bxcommon.utils import config, logger
# TODO port this to sockets soon and remove json serialization perf hit on the node.
from bxcommon.utils.class_json_encoder import ClassJsonEncoder


def fetch_config(node_id):
    # Should only be used for test networks.
    node_url = BxApiRoutes.node.format(node_id)
    opts = http_service.get_json(node_url)
    logger.debug("Retrieved config for id {0} : {1}".format(node_id, opts))

    if opts:
        return NodeModel(**opts)
    else:
        return None


def fetch_outbound_peers(node_id):
    node_url = BxApiRoutes.node_peers.format(node_id)
    outbound_peers = http_service.get_json(node_url)
    logger.debug("Retrieved outbound peers for id {0} : {1}".format(node_id, outbound_peers))

    if not outbound_peers:
        logger.warn("This node has no outbound peers.")
        return []

    outbound_peers = [OutboundPeerModel(**o) for o in outbound_peers]

    config.blocking_resolve_peers(outbound_peers)

    return outbound_peers


def submit_sid_space_full_event(node_id):
    submit_node_event(NodeEventModel(node_id=node_id, event_type=NodeEventType.SID_SPACE_FULL))


def submit_node_online_event(node_id):
    submit_node_event(NodeEventModel(node_id=node_id, event_type=NodeEventType.ONLINE))


def submit_node_offline_event(node_id):
    submit_node_event(NodeEventModel(node_id=node_id, event_type=NodeEventType.OFFLINE))


def submit_peer_connection_error_event(node_id, peer_ip, peer_port):
    submit_node_event(
        NodeEventModel(node_id=node_id, event_type=NodeEventType.PEER_CONN_ERR, peer_ip=peer_ip, peer_port=peer_port))


def submit_node_event(node_event_model):
    node_event_model.timestamp = str(time.time())
    logger.debug("Submitting event for node {0} {1}"
                 .format(node_event_model.node_id, json.dumps(node_event_model, cls=ClassJsonEncoder)))
    url = BxApiRoutes.node_event.format(node_event_model.node_id)
    http_service.post_json(url, node_event_model)


def register_node(node_model):
    if not node_model:
        raise ValueError("Missing node model.")

    # Let the SDN know who this is.
    # SDN determines peers and returns full config.
    node_config = http_service.post_json(BxApiRoutes.nodes, node_model)

    logger.debug("Registered node. Response: {}".format(json.dumps(node_config, cls=ClassJsonEncoder)))

    if not node_config:
        raise EnvironmentError("Unable to reach SDN and register this node. Please check connection.")

    return NodeModel(**node_config)
