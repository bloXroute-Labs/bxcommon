from typing import List, Optional

from bxcommon import constants
from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.connection_type import ConnectionType


def connections(connections: List[AbstractConnection]) -> str:
    """
    Formats list of connections to a string logged in stats
    :param connections: list of connections
    :return: formatted string
    """

    return ", ".join(connection(conn) for conn in connections)


def connection(connection: AbstractConnection) -> str:
    """
    Formats connection to a string logged in stats
    :param connection: Connection
    :return: formatted string
    """

    return "{} - {}".format(connection.peer_desc, _format_connection_type(connection))


def duration(duration_ms: float) -> str:
    """
    Formats duration into a string logged in stats

    :param duration_ms: Duration in milliseconds
    :return: formatted duration
    """

    return "{:.2f}ms".format(duration_ms)


def timespan(start_timestamp_s: float, end_timestamp_s: float) -> str:
    """
    Calculates and formats timespan between start and end, and formats to a string logged in stats

    :param start_timestamp_s: start timestamp in seconds
    :param end_timestamp_s: end timestamp in seconds
    :return: formatted string
    """

    duration_ms = (end_timestamp_s - start_timestamp_s) * 1000
    return duration(duration_ms)


def percentage(percentage: float) -> str:
    """
    Formats percentage into a string logged in stats

    :param duration_ms: Percentage
    :return: formatted duration
    """

    return "{:.2f}%".format(percentage)


def ratio(first_value: float, second_value: float) -> str:
    """
    Calculates ratio of two values and formats the result
    :param first_value: first value
    :param second_value: second value
    :return: formatted ratio
    """

    ratio = 100 - float(first_value) / second_value * 100
    return percentage(ratio)


def _format_connection_type(connection: AbstractConnection) -> Optional[str]:
    if connection.CONNECTION_TYPE == ConnectionType.GATEWAY or \
            connection.network_num == constants.ALL_NETWORK_NUM:
        return "G"

    if connection.CONNECTION_TYPE == ConnectionType.RELAY:
        return "R"

    return connection.CONNECTION_TYPE
