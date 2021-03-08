# pyre-ignore-all-errors
# TODO: this file should be bxgateway, since it depends on bxgateway opts

import json
import os
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING, Union, Dict, Any
from argparse import Namespace

from bxcommon.models.bdn_account_model_base import BdnAccountModelBase
from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.models.blockchain_peer_info import BlockchainPeerInfo
from bxcommon.models.node_model import NodeModel
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.utils import model_loader, config
from bxutils import log_messages
from bxutils import logging
from bxutils.encoding.json_encoder import EnhancedJSONEncoder

logger = logging.get_logger(__name__)

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.common_opts import CommonOpts


@dataclass
class CacheNetworkInfo:
    source_version: str
    relay_peers: List[OutboundPeerModel]
    blockchain_networks: Dict[int, BlockchainNetworkModel]
    blockchain_peers: List[BlockchainPeerInfo]
    node_model: NodeModel
    accounts: Dict[str, Union[BdnAccountModelBase, Any]]


def update_cache_file(
    opts: "CommonOpts",
    potential_relay_peers: Optional[List[OutboundPeerModel]] = None,
    blockchain_peers: Optional[List[BlockchainPeerInfo]] = None,
    accounts: Optional[Dict[str, Optional[BdnAccountModelBase]]] = None
) -> None:
    data = read(opts)
    node_model = model_loader.load_model(NodeModel, opts.__dict__)
    if data is None:
        data = CacheNetworkInfo(
            source_version=opts.source_version,
            relay_peers=potential_relay_peers,
            blockchain_networks=opts.blockchain_networks,
            blockchain_peers=blockchain_peers,
            node_model=node_model,
            accounts=accounts
        )
    else:
        data.blockchain_networks = opts.blockchain_networks
        data.node_model = node_model
        if potential_relay_peers is not None:
            data.relay_peers = potential_relay_peers
        if blockchain_peers is not None:
            data.blockchain_peers = blockchain_peers
        if accounts is not None:
            if data.accounts:
                data.accounts.update(accounts)
            else:
                data.accounts = accounts

    try:
        cookie_file_path = config.get_data_file(opts.cookie_file_path)
        os.makedirs(os.path.dirname(cookie_file_path), exist_ok=True)
        with open(cookie_file_path, "w") as cookie_file:
            json.dump(data, cookie_file, indent=4, cls=EnhancedJSONEncoder)
    # pylint: disable=broad-except
    except Exception as e:
        logger.error(
            "Failed when tried to write to cache file: {} with exception: {}",
            opts.cookie_file_path,
            e
        )


def read(opts: Union["CommonOpts", Namespace]) -> Optional[CacheNetworkInfo]:
    cache_file_info = None
    enable_node_cache = opts.__dict__.get("enable_node_cache", False)
    relative_path = opts.__dict__.get("cookie_file_path", None)
    if enable_node_cache and relative_path is not None:
        try:
            cookie_file_path = config.get_data_file(relative_path)
            if os.path.exists(cookie_file_path):
                with open(cookie_file_path, "r") as cookie_file:
                    cache_file_info = model_loader.load_model(CacheNetworkInfo, json.load(cookie_file))
                    if cache_file_info.source_version != opts.source_version:
                        os.remove(cookie_file_path)
            else:
                logger.warning(log_messages.READ_CACHE_FILE_WARNING, cookie_file_path)
        # pylint: disable=broad-except
        except Exception as e:
            logger.error(
                "Failed when tried to read from cache file: {} with exception: {}",
                relative_path,
                str(e)
            )
    return cache_file_info
