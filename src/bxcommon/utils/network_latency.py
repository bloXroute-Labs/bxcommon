from typing import List

from bxcommon import constants
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.utils import ping_latency
from bxcommon.utils.ping_latency import NodeLatencyInfo
from bxutils import logging

logger = logging.get_logger(__name__)


def get_best_relays_by_ping_latency_one_per_country(relays: List[OutboundPeerModel], countries_count: int) -> List[
    OutboundPeerModel]:
    """
    get best relay by pinging each relay and check its latency calculate with its inbound peers
    :param relays: list of relays
    :param countries_count: number of countries to return best relay for (one per country)
    :return:
    """
    if len(relays) == 1:
        logger.debug("First (and only) recommended relay from api is: {}".format(relays[0]))
        return relays

    relays_ping_latency = ping_latency.get_ping_latencies(relays)
    sorted_ping_latencies = sorted(relays_ping_latency, key=lambda relay_ts: relay_ts.latency)
    best_relays_by_latency = _get_best_relay_latencies_one_per_country(sorted_ping_latencies, relays, countries_count)
    logger.trace("Best relays by latency by country ({}): {}", countries_count, best_relays_by_latency)

    # if best_relay_by_latency's latency is less than RELAY_LATENCY_THRESHOLD_MS, select api's relay
    best_relay_node = relays[0] if best_relays_by_latency[0].latency < constants.NODE_LATENCY_THRESHOLD_MS else \
        best_relays_by_latency[0].node

    logger.info(
        "First recommended relay from api is: {} with {}, "
        "fastest ping latency relay is: {} with {}, selected relay is: {}.  Received relays from api: {}",
        relays[0].ip, "".join([_format_latency(relay.latency) for relay in relays_ping_latency if relay.node == relays[0]]),
        sorted_ping_latencies[0].node.ip, _format_latency(sorted_ping_latencies[0].latency),
        best_relay_node.ip,
        ", ".join(
            [f"{relay_latency.node.ip} with {_format_latency(relay_latency.latency)}"
             for relay_latency in relays_ping_latency]
        )
    )

    result_relays = [best_relay_node]

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
            ping_latency_threshold_by_country[
                relay_country] = constants.FASTEST_PING_LATENCY_THRESHOLD_PERCENT * relay_latency.latency
        elif relay_latency.latency - fastest_latencies_by_country[relay_country].latency < \
                ping_latency_threshold_by_country[relay_country] and \
                relays.index(relay_latency.node) < relays.index(best_latencies_by_country[relay_country].node):
            best_latencies_by_country[relay_country] = relay_latency

    sorted_latencies_by_country = list(
        map(lambda dic_item: dic_item[1],
            sorted(best_latencies_by_country.items(), key=lambda dic_item: dic_item[1].latency)))

    if countries_count > len(sorted_latencies_by_country):
        return sorted_latencies_by_country
    else:
        return sorted_latencies_by_country[:countries_count]


def _format_latency(latency_ms: float) -> str:
    if latency_ms < constants.PING_TIMEOUT_S * 2000:
        return f"latency {latency_ms} ms"

    return "latency timeout"
