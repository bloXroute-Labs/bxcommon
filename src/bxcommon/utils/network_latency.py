from typing import List, Optional, Set

from bxcommon import constants
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.utils import ping_latency
from bxcommon.utils.ping_latency import NodeLatencyInfo
from bxutils import logging

logger = logging.get_logger(__name__)


def get_best_relays_by_ping_latency_one_per_country(
    relays: List[OutboundPeerModel], countries_count: int, current_relays: Optional[Set[OutboundPeerModel]] = None
) -> List[OutboundPeerModel]:
    """
    get best relay by pinging each relay and check its latency calculate with its inbound peers
    :param relays: list of relays
    :param countries_count: number of countries to return best relay for (one per country)
    :param current_relays: (for gateway use only) set of relays that gateway is currently connected to
    :return:
    """
    if len(relays) == 1:
        logger.debug("First (and only) recommended relay from api is: {}", relays[0])
        return relays

    relays_ping_latency = ping_latency.get_ping_latencies(relays)
    sorted_ping_latencies = sorted(relays_ping_latency, key=lambda relay_ts: relay_ts.latency)
    best_relays_by_latency = _get_best_relay_latencies_one_per_country(sorted_ping_latencies, relays, countries_count)
    logger.trace("Best relays by latency by country ({}): {}", countries_count, best_relays_by_latency)

    # if the absolute between fastest relay and recommended relay latency is less than NODE_LATENCY_THRESHOLD_MS,
    # select api's relay
    first_recommended_relay_latency = _get_node_latency_from_list(relays_ping_latency, relays[0].node_id)
    if (
        abs(best_relays_by_latency[0].latency - first_recommended_relay_latency)
        < constants.NODE_LATENCY_THRESHOLD_MS
    ):
        best_relay_node = relays[0]
    else:
        best_relay_node = best_relays_by_latency[0].node

    # for gateways only
    if current_relays is not None and len(current_relays) == 1 and best_relay_node not in current_relays:
        current_relay = next(iter(current_relays))
        if current_relay in relays:
            current_relay_latency = _get_node_latency_from_list(relays_ping_latency, current_relay.node_id)
            best_relay_node_latency = _get_node_latency_from_list(relays_ping_latency, best_relay_node.node_id)
            if current_relay_latency - best_relay_node_latency < constants.GATEWAY_SWAP_RELAYS_LATENCY_THRESHOLD_MS:
                best_relay_node = current_relay

    logger.info("Latency results for potential relays: [{}]",
                ", ".join([f"{relay_latency.node.ip} with {_format_latency(relay_latency.latency)}" for relay_latency in
                          sorted_ping_latencies]))
    logger.info("BDN recommended relay {} with {}. Node selected {}",
                relays[0].ip,
                "".join([_format_latency(relay.latency) for relay in relays_ping_latency if relay.node == relays[0]]),
                best_relay_node.ip)

    result_relays = [best_relay_node]

    if countries_count > 1:
        for extra_relay_latencies in best_relays_by_latency:
            if extra_relay_latencies.node.node_id != best_relay_node.node_id and \
                    extra_relay_latencies.node.get_country() != best_relay_node.get_country():
                result_relays.append(extra_relay_latencies.node)

    if len(result_relays) > 1:
        logger.info("Selected backup relays: {}",
                    ", ".join([f"{backup.ip} from {backup.get_country()}" for backup in result_relays[1:]]))

    return result_relays


def _get_best_relay_latencies_one_per_country(
        sorted_ping_latencies: List[NodeLatencyInfo], relays: List[OutboundPeerModel], countries_count: int
) -> List[NodeLatencyInfo]:
    fastest_latencies_by_country = {}
    best_latencies_by_country = {}
    ping_latency_threshold_by_country = {}

    for relay_latency in sorted_ping_latencies:
        relay = relay_latency.node
        relay_country = relay.get_country()

        if relay_country not in fastest_latencies_by_country:
            fastest_latencies_by_country[relay_country] = relay_latency
            best_latencies_by_country[relay_country] = relay_latency
            ping_latency_threshold_by_country[relay_country] = \
                constants.FASTEST_PING_LATENCY_THRESHOLD_PERCENT * relay_latency.latency
        elif relay_latency.latency - fastest_latencies_by_country[relay_country].latency < \
                ping_latency_threshold_by_country[relay_country] and \
                relays.index(relay_latency.node) < relays.index(best_latencies_by_country[relay_country].node):
            best_latencies_by_country[relay_country] = relay_latency

    sorted_latencies_by_country = list(
        map(
                lambda dic_item: dic_item[1],
                sorted(best_latencies_by_country.items(), key=lambda dic_item: dic_item[1].latency)
            )
    )

    if countries_count > len(sorted_latencies_by_country):
        return sorted_latencies_by_country
    else:
        return sorted_latencies_by_country[:countries_count]


def _format_latency(latency_ms: float) -> str:
    if latency_ms < constants.PING_TIMEOUT_S * 2000:
        return f"latency {latency_ms} ms"

    return "latency timeout"


def _get_node_latency_from_list(node_latencies: List[NodeLatencyInfo], node_id: Optional[str]) -> float:
    for node_latency in node_latencies:
        if node_latency.node.node_id == node_id:
            return node_latency.latency
    return constants.PING_INTERVAL_S * 1000
