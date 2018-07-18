import struct

from bxcommon import constants
from bxcommon.messages.message import Message


class GetTxsDetailsMessage(Message):
    """
    Message used to request information about transactions with specified short ids.
    Node needs to reply with TxsWithShortIdsMessage
    """

    def __init__(self, short_ids=None, buf=None):

        """
        Constructor. Expects list of short ids or message bytes.

        :param short_ids: list of short ids
        :param buf: message bytes
        """

        if buf is None:
            buf = self._serialize_short_ids(short_ids)
            super(GetTxsDetailsMessage, self).__init__('gettxs', len(buf) - constants.HDR_COMMON_OFF, buf)
        else:
            assert not isinstance(buf, str)
            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._short_ids = None

    def short_ids(self):
        if self._short_ids is None:
            self._deserialize_short_ids()

        return self._short_ids

    def _serialize_short_ids(self, short_ids):
        msg_size = constants.HDR_COMMON_OFF + constants.INT_LEN + len(short_ids) * constants.INT_LEN

        buf = bytearray(msg_size)

        off = constants.HDR_COMMON_OFF

        struct.pack_into('<L', buf, off, len(short_ids))
        off += constants.INT_LEN

        for short_id in short_ids:
            struct.pack_into('<L', buf, off, short_id)
            off += constants.INT_LEN

        return buf

    def _deserialize_short_ids(self):
        short_ids = []

        off = constants.HDR_COMMON_OFF

        short_ids_count, = struct.unpack_from('<L', self.buf, off)
        off += constants.INT_LEN

        for index in range(short_ids_count):
            short_id, = struct.unpack_from('<L', self.buf, off)
            short_ids.append(short_id)
            off += constants.INT_LEN

        self._short_ids = short_ids
