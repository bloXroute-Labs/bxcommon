import logging
from io import BytesIO

import msgpack
import sys

from bxutils import constants
from bxutils import log_messages
from bxutils.logging.fluentd_overflow_handler_type import OverflowHandlerType

logger = logging.getLogger(__name__)


def overflow_handler_print(pending_records_buffer, file_obj=sys.stdout):
    logger.error(log_messages.FLUENTD_LOGGER_BUFFER_OVERFLOW)
    unpacker = msgpack.Unpacker(BytesIO(pending_records_buffer))
    for unpacked in unpacker:
        print(unpacked, file=file_obj)


def overflow_handler_ignore(_pending_records_buffer):
    logger.error(log_messages.FLUENTD_LOGGER_BUFFER_OVERFLOW)


overflow_handler_map = {
    OverflowHandlerType.Ignore: overflow_handler_ignore,
    OverflowHandlerType.Print: overflow_handler_print
}

overflow_handler = overflow_handler_map[constants.FLUENTD_OVERFLOW_HANDLER]
