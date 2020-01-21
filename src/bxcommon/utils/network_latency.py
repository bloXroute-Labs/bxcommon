from typing import List

from bxcommon import constants
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.utils import ping_latency
from bxutils import logging

logger = logging.get_logger(__name__)


def get_best_relay_by_ping_latency(relays: List[OutboundPeerModel]) -> OutboundPeerModel:
    """
    get best relay by pinging each relay and check its latency calculate with its inbound peers
    :param relays:
    :return:
    """
    if len(relays) == 1:
        logger.debug("First (and only) recommended relay from api is: {}".format(relays[0]))
        return relays[0]

    relays_ping_latency = ping_latency.get_ping_latencies(relays)
    sorted_ping_latencies = sorted(relays_ping_latency, key=lambda relay_ts: relay_ts.latency)
    best_relay_by_latency = _get_best_relay(sorted_ping_latencies, relays)

    # if best_relay_by_latency's latency is less than RELAY_LATENCY_THRESHOLD_MS, select api's relay
    best_relay_node = relays[0] if best_relay_by_latency.latency < constants.NODE_LATENCY_THRESHOLD_MS else best_relay_by_latency.node

    logger.info(
        "First recommended relay from api is: {} with latency {} ms. "
        "Fastest ping latency relay is: {} with latency {} ms. Selected relay is: {}. Received relays from api: {}",
        relays[0].ip, "".join([str(relay.latency) for relay in relays_ping_latency if relay.node == relays[0]]),
        sorted_ping_latencies[0].node.ip, sorted_ping_latencies[0].latency,
        best_relay_node.ip,
        ", ".join(
            [f"{relay_latency.node.ip} with latency {relay_latency.latency} ms" for relay_latency in relays_ping_latency]
        )

    )

    return best_relay_node


def _get_best_relay(
        sorted_ping_latencies: List[ping_latency.NodeLatencyInfo], relays: List[OutboundPeerModel]
) -> ping_latency.NodeLatencyInfo:

    fastest_relay = sorted_ping_latencies[0]
    return_best_relay = fastest_relay
    ping_latency_threshold = constants.FASTEST_PING_LATENCY_THRESHOLD_PERCENT * fastest_relay.latency

    for relay in sorted_ping_latencies[1:]:
        if relay.latency - fastest_relay.latency < ping_latency_threshold and \
                relays.index(relay.node) < relays.index(return_best_relay.node):
                return_best_relay = relay
        else:
            break

    return return_best_relay

