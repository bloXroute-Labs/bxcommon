from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    # pylint: disable=R0401
    from bxcommon.connections.abstract_connection import AbstractConnection

SUFFIXES = ["bytes", "kB", "MB", "GB"]


def byte_count(num_bytes: float) -> str:
    i = 0
    while num_bytes > 1024 and i < len(SUFFIXES):
        num_bytes /= 1024
        i += 1

    return f"{int(num_bytes)} {SUFFIXES[i]}"


def connections(conns: List["AbstractConnection"]) -> str:
    """
    Formats list of connections to a string logged in stats
    :param conns: list of connections
    :return: formatted string
    """

    return ", ".join(conn.format_connection_desc for conn in conns if conn is not None)


def connection(conn: Optional["AbstractConnection"]) -> str:
    """
    Formats connection to a string logged in stats
    :param conn: Connection
    :return: formatted string
    """

    if conn is None:
        return "<None>"

    return conn.format_connection_desc


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


def percentage(percent: float) -> str:
    """
    Formats percentage into a string logged in stats

    :param percent: Percentage
    :return: formatted duration
    """

    return "{:.2f}%".format(percent)


def ratio(first_value: float, second_value: float) -> str:
    """
    Calculates ratio of two values and formats the result
    :param first_value: first value
    :param second_value: second value
    :return: formatted ratio
    """
    return percentage(100 - float(first_value) / second_value * 100)
