import struct

from bxcommon import constants
from bxcommon.messages.message import Message


class GetTxsDetailsMessage(Message):
    """
    Message used to request information about services with specified short ids.
    Node needs to reply with TxsWithShortIdsMessage
    """

    def __init__(self, short_ids=None, buf=None):

        """
        Constructor. Expects list of short ids or message bytes.

        :param short_ids: list of short ids
        :param buf: message bytes
        """

        if buf is None:
            buf = self._short_ids_to_bytes(short_ids)
            super(GetTxsDetailsMessage, self).__init__('gettxs', len(buf) - constants.HDR_COMMON_OFF, buf)
        else:
            if isinstance(buf, str):
                raise TypeError("Buffer can't be string")

            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._short_ids = None

    def get_short_ids(self):
        if self._short_ids is None:
            self._parse()

        return self._short_ids

    def _short_ids_to_bytes(self, short_ids):
        msg_size = constants.HDR_COMMON_OFF + constants.INTEGER_SIZE_IN_BYTES + \
                   len(short_ids) * constants.INTEGER_SIZE_IN_BYTES

        buf = bytearray(msg_size)

        off = constants.HDR_COMMON_OFF

        struct.pack_into('<L', buf, off, len(short_ids))
        off += constants.INTEGER_SIZE_IN_BYTES

        for short_id in short_ids:
            struct.pack_into('<L', buf, off, short_id)
            off += constants.INTEGER_SIZE_IN_BYTES

        return buf

    def _parse(self):
        short_ids = []

        off = constants.HDR_COMMON_OFF

        short_ids_count, = struct.unpack_from('<L', self.buf, off)
        off += constants.INTEGER_SIZE_IN_BYTES

        for index in range(short_ids_count):
            short_id, = struct.unpack_from('<L', self.buf, off)
            short_ids.append(short_id)
            off += constants.INTEGER_SIZE_IN_BYTES

        self._short_ids = short_ids
