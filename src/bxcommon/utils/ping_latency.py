import subprocess
from typing import List, NamedTuple

from bxcommon import constants
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.utils.concurrency.thread_pool import ThreadPool
from bxutils import log_messages
from bxutils import logging

logger = logging.get_logger(__name__)


class NodeLatencyInfo(NamedTuple):
    node: OutboundPeerModel
    latency: float


def get_ping_latency(outbound_peer: OutboundPeerModel) -> NodeLatencyInfo:
    """
    returns ping latency to the outbound peer
    :param outbound_peer: peer to ping
    """
    try:
        with subprocess.Popen(["ping", "-c", "1", outbound_peer.ip], stdout=subprocess.PIPE) as proc:
            try:
                if proc:
                    output = proc.communicate(timeout=constants.PING_TIMEOUT_S)[0].decode()
                    ping_latency = float(output.split("time=", 1)[1].split("ms", 1)[0])
                else:
                    ping_latency = constants.PING_TIMEOUT_S * 1000
                    logger.debug("Could not ping {} {}.", outbound_peer.node_type, outbound_peer.ip)
            except subprocess.TimeoutExpired:
                ping_latency = constants.PING_TIMEOUT_S * 1000
                logger.debug("Ping to {} {} timed out.", outbound_peer.node_type, outbound_peer.ip)
    # pylint: disable=broad-except
    except Exception as e:
        logger.error(
            log_messages.PING_TRIGGERED_AN_ERROR, outbound_peer.node_type, outbound_peer.ip, e
        )
        ping_latency = constants.PING_TIMEOUT_S * 1000

    return NodeLatencyInfo(outbound_peer, ping_latency)


def get_ping_latencies(outbound_peers: List[OutboundPeerModel]) -> List[NodeLatencyInfo]:
    with ThreadPool(len(outbound_peers), "ping") as executor:
        futures = [executor.submit(get_ping_latency, ip) for ip in outbound_peers]
        results = [future.result() for future in futures]
    return results
