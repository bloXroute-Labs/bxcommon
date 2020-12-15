import time
from ssl import SSLContext
from typing import List, Optional, Dict, Any, cast

from bxcommon.constants import SdnRoutes
from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.models.gateway_settings_model import GatewaySettingsModel
from bxcommon.models.node_event_model import NodeEventModel, NodeEventType
from bxcommon.models.node_model import NodeModel
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.models.bdn_account_model_base import BdnAccountModelBase
from bxcommon.services import http_service
from bxcommon.utils import model_loader, ip_resolver
from bxutils import log_messages
from bxutils import logging
from bxutils.encoding import json_encoder

logger = logging.get_logger(__name__)


def fetch_node_attributes(node_id: str) -> Optional[NodeModel]:
    # Should only be used for test networks.
    node_url = SdnRoutes.node.format(node_id)
    opts = cast(Dict[str, Any], http_service.get_json(node_url))
    logger.trace("Retrieved config for id {0} : {1}", node_id, opts)

    if opts:
        return model_loader.load_model(NodeModel, opts)
    else:
        return None


def _fetch_peers(node_url: str, node_id: Optional[str] = None) -> List[OutboundPeerModel]:
    outbound_peers_response = cast(List[Dict[str, Any]], http_service.get_json(node_url))
    logger.debug(
        "Retrieved outbound peers for node {0} from endpoint {1}: {2}",
        node_id,
        node_url,
        outbound_peers_response
    )

    if not outbound_peers_response:
        logger.warning(log_messages.BDN_RETURNED_NO_PEERS, node_url)
        return []

    outbound_peers = [
        model_loader.load_model(OutboundPeerModel, o) for o in outbound_peers_response
    ]
    ip_resolver.blocking_resolve_peers(outbound_peers)
    return outbound_peers


def fetch_potential_relay_peers_by_network(node_id: str, network_num: int) -> Optional[List[OutboundPeerModel]]:
    node_url = SdnRoutes.node_potential_relays_by_network.format(node_id, network_num)
    return _fetch_peers(node_url, node_id)


def fetch_gateway_peers(node_id: str, request_streaming: bool) -> Optional[List[OutboundPeerModel]]:
    node_url = SdnRoutes.node_gateways.format(node_id, request_streaming)
    return _fetch_peers(node_url, node_id)


def fetch_remote_blockchain_peer(node_id: str) -> Optional[OutboundPeerModel]:
    node_url = SdnRoutes.node_remote_blockchain.format(node_id)
    peers = _fetch_peers(node_url, node_id)
    if len(peers) < 1:
        logger.warning(log_messages.BDN_RETURNED_UNEXPECTED_NUMBER_OF_PEERS)
        return None
    else:
        logger.debug("Ordered potential remote blockchain peers: {}", peers)
        return peers[0]


def fetch_blockchain_network(protocol_name: str, network_name: str) -> Optional[BlockchainNetworkModel]:
    node_url = SdnRoutes.blockchain_network.format(protocol_name, network_name)
    blockchain_network = cast(Dict[str, Any], http_service.get_json(node_url))

    if blockchain_network is None:
        return None

    blockchain_network = model_loader.load_model(BlockchainNetworkModel, blockchain_network)

    return blockchain_network


def fetch_gateway_settings(node_id: str) -> GatewaySettingsModel:
    node_url = SdnRoutes.gateway_settings.format(node_id)
    gateway_settings = cast(Dict[str, Any], http_service.get_json(node_url))

    if not gateway_settings:
        gateway_settings = GatewaySettingsModel()
    else:
        gateway_settings = model_loader.load_model(GatewaySettingsModel, gateway_settings)

    return gateway_settings


def fetch_blockchain_networks() -> Dict[int, BlockchainNetworkModel]:
    node_url = SdnRoutes.blockchain_networks
    sdn_blockchain_networks = http_service.get_json(node_url)

    if not sdn_blockchain_networks:
        logger.warning(log_messages.BDN_CONTAINS_NO_CONFIGURED_NETWORKS)
        return {}

    assert isinstance(sdn_blockchain_networks, List)
    blockchain_network_models = [model_loader.load_model(BlockchainNetworkModel, b) for b in sdn_blockchain_networks]
    blockchain_network_dict = {network_model.network_num: network_model for network_model in blockchain_network_models}
    return blockchain_network_dict


def fetch_quota_status(account_id: str) -> Optional[Dict[str, Any]]:
    result = http_service.get_json_with_payload(SdnRoutes.quota_status, {"account_id": account_id})
    if result:
        result = cast(Dict[str, Any], result)
        return result
    else:
        return None


def submit_sid_space_switch(node_id: str) -> None:
    submit_node_event(NodeEventModel(node_id=node_id, event_type=NodeEventType.SID_SPACE_SWITCH))


def submit_sid_space_full_event(node_id: str) -> None:
    submit_node_event(NodeEventModel(node_id=node_id, event_type=NodeEventType.SID_SPACE_FULL))


def submit_peer_connection_error_event(node_id: str, peer_ip: str, peer_port: int) -> None:
    submit_peer_connection_event(NodeEventType.PEER_CONN_ERR, node_id, peer_ip, peer_port)


def submit_peer_connection_event(
    event_type: NodeEventType, node_id: str, peer_ip: str, peer_port: int, payload: Optional[str] = None
) -> None:
    submit_node_event(
        # pyre-fixme[6]: Expected `str` for 5th param but got `Optional[str]`.
        NodeEventModel(node_id=node_id, event_type=event_type, peer_ip=peer_ip, peer_port=peer_port, payload=payload)
    )


def submit_gateway_switching_relays_event(node_id: str) -> None:
    submit_node_event(NodeEventModel(node_id=node_id, event_type=NodeEventType.SWITCHING_RELAYS))


def submit_gateway_inbound_connection(node_id: str, peer_id: str) -> None:
    http_service.post_json(SdnRoutes.gateway_inbound_connection.format(node_id), peer_id)


def submit_tx_synced_event(node_id: str) -> None:
    submit_node_event(NodeEventModel(node_id=node_id, event_type=NodeEventType.TX_SERVICE_FULLY_SYNCED))


def submit_tx_not_synced_event(node_id: str) -> None:
    submit_node_event(NodeEventModel(node_id=node_id, event_type=NodeEventType.TX_SERVICE_NOT_SYNCED))


def submit_notify_offline_event(node_id: str) -> None:
    submit_node_event(NodeEventModel(node_id=node_id, event_type=NodeEventType.NOTIFY_OFFLINE))


def delete_gateway_inbound_connection(node_id: str, peer_id: str) -> None:
    http_service.delete_json(SdnRoutes.gateway_inbound_connection.format(node_id), peer_id)


def submit_node_event(node_event_model: NodeEventModel) -> None:
    node_event_model.timestamp = str(time.time())
    logger.trace("Submitting event for node {0} {1}", node_event_model.node_id, json_encoder.to_json(node_event_model))
    url = SdnRoutes.node_event.format(node_event_model.node_id)
    http_service.post_json(url, node_event_model)


def register_node(node_model: NodeModel) -> NodeModel:
    if not node_model:
        raise ValueError("Missing node model.")

    # Let the SDN know who this is.
    # SDN determines peers and returns full config.
    node_config = cast(Dict[str, Any], http_service.post_json(SdnRoutes.nodes, node_model))

    logger.trace("Registered node. Response: {}", json_encoder.to_json(node_config))

    if not node_config:
        raise EnvironmentError("Unable to reach SDN and register this node. Please check connection.")

    registered_node_model = model_loader.load_model(NodeModel, node_config)

    if not registered_node_model.source_version:
        raise ValueError(f"Source version {node_model.source_version} is no longer supported. Please upgrade to the "
                         f"latest version")

    if registered_node_model.blockchain_network_num == -1:
        raise ValueError(f"The blockchain network number {node_model.blockchain_network_num} does not exists. Please "
                         f"check the blockchain network startup parameters")

    return registered_node_model


def reset_pool(ssl_context: SSLContext) -> None:
    http_service.update_http_ssl_context(ssl_context)


def fetch_account_model(account_id: str) -> Optional[BdnAccountModelBase]:
    account_url = SdnRoutes.account.format(account_id)
    response = cast(Dict[str, Any], http_service.get_json(account_url))

    if response:
        return model_loader.load_model(BdnAccountModelBase, response)
    else:
        return None
