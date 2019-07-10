import struct

from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v4.message_v4 import MessageV4


class GetTxsMessageV4(MessageV4):
    MESSAGE_TYPE = BloxrouteMessageType.GET_TRANSACTIONS

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

        self._short_ids = None
        if buf is None:
            buf = self._short_ids_to_bytes(short_ids)
            super(GetTxsMessageV4, self).__init__(self.MESSAGE_TYPE, len(buf) - constants.BX_HDR_COMMON_OFF, buf)
        else:
            if isinstance(buf, str):
                raise TypeError("Buffer can't be string")

            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._payload_len = None
            self._payload = None

    def get_short_ids(self):
        if self._short_ids is None:
            self._parse()

        return self._short_ids

    def _short_ids_to_bytes(self, short_ids):
        msg_size = constants.BX_HDR_COMMON_OFF + constants.UL_INT_SIZE_IN_BYTES + \
                   len(short_ids) * constants.UL_INT_SIZE_IN_BYTES

        buf = bytearray(msg_size)

        off = constants.BX_HDR_COMMON_OFF

        struct.pack_into('<L', buf, off, len(short_ids))
        off += constants.UL_INT_SIZE_IN_BYTES

        for short_id in short_ids:
            struct.pack_into('<L', buf, off, short_id)
            off += constants.UL_INT_SIZE_IN_BYTES

        return buf

    def _parse(self):
        short_ids = []

        off = constants.BX_HDR_COMMON_OFF

        short_ids_count, = struct.unpack_from('<L', self.buf, off)
        off += constants.UL_INT_SIZE_IN_BYTES

        for index in range(short_ids_count):
            short_id, = struct.unpack_from('<L', self.buf, off)
            short_ids.append(short_id)
            off += constants.UL_INT_SIZE_IN_BYTES

        self._short_ids = short_ids

    def __repr__(self):
        return "GetTxsMessage<num_short_ids: {}>".format(len(self.get_short_ids()))
