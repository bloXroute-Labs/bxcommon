import uuid

from bxcommon import constants
from bxutils import logging

logger = logging.get_logger(__name__)


def to_bytes(string_input):
    if not string_input:
        return constants.EMPTY_SOURCE_ID

    try:
        raw = uuid.UUID(string_input).bytes
    except ValueError as _e:
        logger.trace("Invalid node ID: {}", string_input)
        return constants.EMPTY_SOURCE_ID
    return raw


def from_bytes(bytes_input):
    if not bytes_input:
        return None
    if not bytes_input.rstrip(constants.MSG_NULL_BYTE):
        return None
    return str(uuid.UUID(bytes=bytes_input))
