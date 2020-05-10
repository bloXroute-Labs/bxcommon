import json
import os
from argparse import Namespace
from dataclasses import dataclass
from typing import List, Optional

from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.models.node_model import NodeModel
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.utils import model_loader, config
from bxutils import log_messages
from bxutils import logging
from bxutils.encoding.json_encoder import EnhancedJSONEncoder

logger = logging.get_logger(__name__)


@dataclass
class CacheNetworkInfo:
    source_version: str
    relay_peers: List[OutboundPeerModel]
    blockchain_network: List[BlockchainNetworkModel]
    blockchain_networks: List[BlockchainNetworkModel]
    node_model: NodeModel


def update(opts: Namespace, potential_relay_peers: List[OutboundPeerModel]):
    try:
        cookie_file_path = config.get_data_file(opts.cookie_file_path)
        os.makedirs(os.path.dirname(cookie_file_path), exist_ok=True)
        with open(cookie_file_path, "r") as cookie_file:
            data = json.load(cookie_file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        data = {}

    # if gateway was upgraded, its version number has changed and its relays are no longer relevant
    if "source_version" in data and data["source_version"] != opts.source_version:
        data = {}

    cache_network_info = CacheNetworkInfo(
        source_version=opts.source_version,
        relay_peers=list(potential_relay_peers),
        blockchain_network=[blockchain for blockchain in opts.blockchain_networks
                            if opts.blockchain_network_num == blockchain.network_num],
        blockchain_networks=opts.blockchain_networks,
        node_model=model_loader.load_model(NodeModel, opts.__dict__)
    )
    cache_info = {
        "source_version": opts.source_version,
        "relay_peers": [relay.__dict__ for relay in cache_network_info.relay_peers],
        "blockchain_network": [blockchain_network.__dict__ for blockchain_network in
                               cache_network_info.blockchain_network],
        "blockchain_networks": cache_network_info.blockchain_networks,
        "node_model": cache_network_info.node_model
    }
    data.update(cache_info)

    try:
        with open(config.get_data_file(opts.cookie_file_path), "w") as cookie_file:
            json.dump(data, cookie_file, indent=4, cls=EnhancedJSONEncoder)
    # pylint: disable=broad-except
    except Exception as e:
        logger.error(
            "Failed when tried to write to cache file: {} with exception: {}",
            opts.cookie_file_path,
            e
        )


def read(opts: Namespace) -> Optional[CacheNetworkInfo]:
    cache_file_info = None
    if not opts.enable_node_cache:
        return cache_file_info
    if not opts.cookie_file_path:
        return cache_file_info
    try:
        relative_path = config.get_data_file(opts.cookie_file_path)
        if os.path.exists(relative_path):
            with open(relative_path, "r") as cookie_file:
                cache_file_info = model_loader.load_model(CacheNetworkInfo, json.load(cookie_file))
        else:
            logger.error(log_messages.READ_CACHE_FILE_ERROR)
    # pylint: disable=broad-except
    except Exception as e:
        logger.error(
            "Failed when tried to read from cache file: {} with exception: {}",
            opts.cookie_file_path,
            e
        )
    return cache_file_info
