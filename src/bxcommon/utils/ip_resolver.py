import re
import socket
import time
from typing import List, Optional

import requests

from bxcommon import constants
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxutils import logging

logger = logging.get_logger(__name__)


def blocking_resolve_ip(net_address: str) -> str:
    tries = 0
    resolved_ip = None
    while resolved_ip is None:
        try:
            resolved_ip = socket.gethostbyname(net_address)
        except socket.error:
            time.sleep(constants.NET_ADDR_INIT_CONNECT_RETRY_INTERVAL_SECONDS)
            resolved_ip = None
            tries += 1

            logger.debug("Unable to resolve address {0}. Retried {1}", net_address, tries)
            if tries >= constants.NET_ADDR_INIT_CONNECT_TRIES:
                raise EnvironmentError("Unable to resolve address {}.".format(net_address))
    assert resolved_ip is not None
    return resolved_ip


def blocking_resolve_peers(peer_models: List[OutboundPeerModel]):
    for peer in peer_models:
        resolved_ip = blocking_resolve_ip(peer.ip)

        if peer.ip != resolved_ip:
            logger.trace("Resolved peer {0} to {1}".format(peer.ip, resolved_ip))
            peer.ip = resolved_ip

    logger.trace("Resolved peers successfully.")


def get_node_public_ip() -> Optional[str]:
    """
    Get the public IP address of the node based on a request to `PUBLIC_IP_ADDR_RESOLVER`. If address cannot be
    resolved, it must be specified as a command line argument

    :return: the resolved IP address
    """
    try:
        get_response = requests.get(constants.PUBLIC_IP_ADDR_RESOLVER).text
        public_ip_addr = re.findall(constants.PUBLIC_IP_ADDR_REGEX, get_response)
        if public_ip_addr:
            return public_ip_addr[0]

        raise ConnectionError("Unable to parse IP from response - response was [{}]".format(get_response))
    except Exception as ex:
        logger.error(
            "Unable to determine public IP address, please specify one manually via the '--external-ip' command line "
            "argument.\n\nDetailed error message:\n\t{}", ex)
        exit(1)
