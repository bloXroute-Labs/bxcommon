import struct

from bxcommon import constants
from bxcommon.messages.bloxroute.message import Message


class VersionMessage(Message):
    """
    Bloxroute message that contains version info.
    """

    BASE_LENGTH = constants.HDR_COMMON_OFF + constants.VERSION_NUM_LEN + constants.NETWORK_NUM_LEN

    def __init__(self, msg_type, payload_len, protocol_version, network_num, buf):
        if protocol_version is not None and network_num is not None:
            if len(buf) < self.BASE_LENGTH:
                raise ValueError("Version message is not long enough.")

            off = self.HEADER_LENGTH
            struct.pack_into("<L", buf, off, protocol_version)

            off += constants.VERSION_NUM_LEN
            struct.pack_into("<L", buf, off, network_num)

        self._protocol_version = None
        self._network_num = None
        super(VersionMessage, self).__init__(msg_type, payload_len, buf)

    def protocol_version(self):
        if self._protocol_version is None:
            off = self.HEADER_LENGTH
            self._protocol_version, = struct.unpack_from("<L", self.buf, off)
        return self._protocol_version

    def network_num(self):
        if self._network_num is None:
            off = self.HEADER_LENGTH + constants.VERSION_NUM_LEN
            self._network_num, = struct.unpack_from("<L", self._memoryview, off)
        return self._network_num
