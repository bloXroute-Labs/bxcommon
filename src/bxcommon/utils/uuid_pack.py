import uuid

from bxutils import logging

from bxcommon import constants

logger = logging.get_logger(__name__)


def to_bytes(string_input):
    if not string_input:
        return constants.MSG_NULL_BYTE * 16

    try:
        raw = uuid.UUID(string_input).bytes
    except ValueError as e:
        logger.error("invalid node id provided {}".format(string_input))
        return constants.MSG_NULL_BYTE * 16
    return raw


def from_bytes(bytes_input):
    if not bytes_input:
        return None
    if not bytes_input.rstrip(constants.MSG_NULL_BYTE):
        return None
    return str(uuid.UUID(bytes=bytes_input))
