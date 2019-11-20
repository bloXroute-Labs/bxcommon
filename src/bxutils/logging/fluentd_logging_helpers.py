import logging
import msgpack
from io import BytesIO

from bxutils import constants
from bxutils.logging.fluentd_overflow_handler_type import OverflowHandlerType

logger = logging.getLogger(__name__)


def overflow_handler_print(pending_records_buffer):
    logger.error("fluentd logger, buffer overflow")
    unpacker = msgpack.Unpacker(BytesIO(pending_records_buffer))
    for unpacked in unpacker:
        print(unpacked)


def overflow_handler_ignore(pending_records_buffer):
    logger.error("fluentd logger, buffer overflow")


overflow_handler_map = {
    OverflowHandlerType.Ignore: overflow_handler_ignore,
    OverflowHandlerType.Print: overflow_handler_print
}

overflow_handler = overflow_handler_map[constants.FLUENTD_OVERFLOW_HANDLER]
